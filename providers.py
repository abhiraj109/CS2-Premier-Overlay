"""Normalize Leetify's documented public responses for the overlay."""

from datetime import datetime
import json
from math import isfinite
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SOURCES = {"matchmaking", "matchmaking_premier", "matchmaking_competitive",
           "matchmaking_competitive_5v5", "matchmaking_wingman"}
OUTCOMES = {"win": "W", "loss": "L", "tie": "T", "draw": "T"}


def number(value: Any) -> float | None:
    if type(value) in (float, int) and abs(value) <= 1_000_000 and isfinite(value):
        return value
    return None


def positive(value: Any) -> float | None:
    value = number(value)
    return value if value is not None and value >= 0 else None


def rating_band(rating: float | None) -> str:
    if rating is None:
        return "unrated"
    for minimum, band in ((30000, "gold"), (25000, "red"), (20000, "pink"),
                          (15000, "purple"), (10000, "blue"), (5000, "lightblue")):
        if rating >= minimum:
            return band
    return "grey"


def time_key(match: dict) -> float:
    try:
        timestamp = datetime.fromisoformat(match.get("finished_at", "").replace("Z", "+00:00"))
        return timestamp.timestamp() if timestamp.tzinfo else 0
    except (ValueError, AttributeError, OSError, OverflowError):
        return 0


def tagged_matches(items: Any) -> list[dict]:
    if not isinstance(items, list):
        return []
    return [
        item for item in items if isinstance(item, dict)
        and isinstance(item.get("data_source"), str) and item["data_source"].lower() in SOURCES
        and isinstance(item.get("id"), str) and item["id"] and time_key(item) > 0
    ]


def match_rows(profile: dict, matches: list, steam_id: str) -> list[dict]:
    by_id = {item["id"]: item for item in tagged_matches(profile.get("recent_matches"))}
    for detail in tagged_matches(matches):
        stats = detail.get("stats")
        player = next((row for row in stats if isinstance(row, dict)
                       and row.get("steam64_id") == steam_id), {}) if isinstance(stats, list) else {}
        outcome = by_id.get(detail["id"], {}).get("outcome")
        if not isinstance(outcome, str) or outcome not in OUTCOMES:
            scores = detail.get("team_scores")
            team = positive(player.get("initial_team_number"))
            if team is not None and isinstance(scores, list):
                teams = {positive(row.get("team_number")): positive(row.get("score"))
                         for row in scores if isinstance(row, dict)}
                if len(teams) == 2 and team in teams and None not in teams and None not in teams.values():
                    own = teams.pop(team)
                    other = next(iter(teams.values()))
                    outcome = "win" if own > other else "loss" if own < other else "tie"
        by_id[detail["id"]] = {
            "finished_at": detail["finished_at"], "outcome": outcome,
            "kills": positive(player.get("total_kills")), "deaths": positive(player.get("total_deaths")),
            "headshots": positive(player.get("total_hs_kills")),
            "rounds": positive(player.get("rounds_count")), "damage": positive(player.get("total_damage")),
            "adr": positive(player.get("dpr")),
        }
    return sorted(by_id.values(), key=time_key, reverse=True)[:20]


def last20(matches: list[dict]) -> tuple[dict, list[dict]]:
    rows = matches[:20]
    kills = [row["kills"] for row in rows if row.get("kills") is not None]
    kd = [(row["kills"], row["deaths"]) for row in rows
          if row.get("kills") is not None and row.get("deaths") is not None]
    kr = [(row["kills"], row["rounds"]) for row in rows
          if row.get("kills") is not None and row.get("rounds")]
    hs = [(row["headshots"], row["kills"]) for row in rows
          if row.get("headshots") is not None and row.get("kills") is not None
          and row["headshots"] <= row["kills"]]
    adr = [(row["damage"] if row.get("damage") is not None else row["adr"] * row["rounds"], row["rounds"])
           for row in rows if row.get("rounds") and (row.get("damage") is not None or row.get("adr") is not None)]
    outcomes = [OUTCOMES.get(value, "?") if isinstance(value, str) else "?" for value in
                (row.get("outcome") for row in rows)]
    resolved = [outcome for outcome in outcomes if outcome != "?"]

    def ratio(pairs: list[tuple], digits: int, multiplier: int = 1) -> float | None:
        numerator = sum(pair[0] for pair in pairs)
        denominator = sum(pair[1] for pair in pairs)
        return round(multiplier * numerator / denominator, digits) if denominator else None

    return {
        "kd": ratio(kd, 2), "kr": ratio(kr, 2), "adr": ratio(adr, 1),
        "avg_kills": round(sum(kills) / len(kills), 1) if kills else None,
        "hs_percent": ratio(hs, 1, 100),
        "win_percent": round(100 * resolved.count("W") / len(resolved), 1) if resolved else None,
        "match_count": len(rows), "matches_with_stats": len(kd),
    }, [{"result": outcome} for outcome in outcomes[:5]]


def parse_profile(profile: dict, steam_id: str, matches: Any = None) -> dict:
    ranks = profile.get("ranks")
    premier = positive(ranks.get("premier")) if isinstance(ranks, dict) else None
    premier = int(premier) if premier and int(premier) == premier else None
    stats, form = last20(match_rows(profile, matches, steam_id))
    name = profile.get("name")
    avatar = profile.get("avatar")
    return {"steam_id": steam_id, "name": name.strip()[:80] if isinstance(name, str) else "",
            "avatar": avatar if isinstance(avatar, str) and avatar.startswith("https://") and len(avatar) < 512 else "",
            "premier_rating": premier, "rating_band": rating_band(premier),
            "last20": stats, "recent_form": form, "source": "Leetify",
            "profile_url": f"https://leetify.com/app/profile/{steam_id}"}


def http_json(url: str, api_key: str = "") -> Any:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "CS2-Premier-OBS-Overlay"})
    if api_key:
        request.add_unredirected_header("Authorization", f"Bearer {api_key}")
    with urlopen(request, timeout=8) as response:
        limit = 20 * 1024 * 1024
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Provider response exceeded the size limit")
        return json.loads(data)


class PrivateProfile(ValueError):
    pass


class LeetifyProvider:
    def fetch(self, steam_id: str) -> dict:
        base = "https://api-public.cs-prod.leetify.com/v3/profile"
        query = urlencode({"steam64_id": steam_id})
        api_key = os.environ.get("LEETIFY_API_KEY", "").strip()
        profile = http_json(f"{base}?{query}", api_key)
        if not isinstance(profile, dict) or profile.get("steam64_id") != steam_id:
            raise ValueError("Unexpected Leetify profile response")
        if profile.get("privacy_mode") in ("private", "hidden"):
            raise PrivateProfile("Leetify profile is private")

        matches = None
        history_error = ""
        retry_after = None
        try:
            response = http_json(f"{base}/matches?{query}", api_key)
            if not isinstance(response, list):
                raise ValueError("Unexpected Leetify match response")
            matches = response
        except HTTPError as exc:
            history_error = f"Match history HTTP {exc.code}"
            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After", "600") if exc.headers else "600"
            if exc.code in (403, 404, 410):
                matches = []
                if not isinstance(profile.get("recent_matches"), list):
                    profile["recent_matches"] = []
            exc.close()
        except (URLError, OSError, ValueError) as exc:
            history_error = f"Match history unavailable ({type(exc).__name__})"
        result = parse_profile(profile, steam_id, matches)
        result.update(history_error=history_error, match_details=matches is not None, retry_after=retry_after)
        return result
