"""Track a single local player's CS2 Game State Integration session."""

from typing import Any
from uuid import uuid4

GSI_ALIVE_SECONDS = 45
GAME_OVER = ("gameover", "over")
MATCH_MODES = {"competitive", "premier", "wingman", "scrimcomp2v2"}
STEAM_ID_BASE = 76561197960265728
FIELDS = {
    "provider": {"appid": int, "steamid": str, "timestamp": int},
    "map": {"name": str, "mode": str, "phase": str, "round": int,
            "team_ct": {"score": int}, "team_t": {"score": int}},
    "round": {"phase": str, "win_team": str},
    "player": {"steamid": str, "name": str, "activity": str, "team": str,
               "match_stats": {"kills": int, "deaths": int, "assists": int, "score": int, "mvps": int}},
}


def section(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def count(value: Any) -> int | None:
    return value if type(value) is int and 0 <= value <= 100000 else None


def pick(value: dict, fields: dict) -> dict:
    selected = {}
    for key, expected in fields.items():
        item = value.get(key)
        if isinstance(expected, dict) and isinstance(item, dict):
            selected[key] = pick(item, expected)
        elif type(item) is expected:
            selected[key] = item[:100] if expected is str else item
        elif key in value and item is None:
            selected[key] = None
    return selected


def merge(target: dict, incoming: dict) -> None:
    for key, value in incoming.items():
        if value is None:
            target.pop(key, None)
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            merge(target[key], value)
        else:
            target[key] = value


class GameState:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.received = 0.0
        self.match_id = ""
        self.local_team = ""
        self.finished = False

    def snapshot(self, now: float) -> dict:
        age = round(max(0, now - self.received), 1) if self.received else None
        connected = age is not None and age <= GSI_ALIVE_SECONDS
        return {"connected": connected, "age_seconds": age,
                "received_at": self.received or None, "data": self.data if connected else {}}

    def ingest(self, payload: dict, now: float) -> tuple | None:
        previously = section(payload.get("previously"))
        payload = pick(payload, FIELDS)
        provider = section(payload.get("provider"))
        old_provider = section(self.data.get("provider"))
        old_map = section(self.data.get("map"))
        incoming_map = section(payload.get("map"))
        old_stamp = old_provider.get("timestamp")
        stamp = provider.get("timestamp")
        account = provider.get("steamid")
        stale = now - self.received > GSI_ALIVE_SECONDS
        account_changed = bool(account and account != old_provider.get("steamid"))
        if not stale and not account_changed and type(stamp) is int and type(old_stamp) is int:
            if stamp < old_stamp:
                return None

        phase = incoming_map.get("phase")
        old_round = count(old_map.get("round"))
        new_round = count(incoming_map.get("round"))
        changed_map = incoming_map.get("name") and incoming_map["name"] != old_map.get("name")
        returned_to_warmup = phase == "warmup" and old_map.get("phase") != "warmup"
        round_reset = old_round is not None and new_round is not None and new_round < old_round
        score_reset = all(section(incoming_map.get(side)).get("score") == 0 for side in ("team_ct", "team_t"))
        new_live_match = phase == "live" and (round_reset or (old_map.get("phase") in GAME_OVER and score_reset))
        if phase == "live" and old_map.get("phase") in GAME_OVER:
            if not (stale or account_changed or changed_map or score_reset or (round_reset and new_round == 0)):
                return None
        cleared_map = "map" in payload and not incoming_map
        removed_map = bool(previously.get("map")) and not incoming_map
        if stale or account_changed or changed_map or returned_to_warmup or new_live_match or cleared_map or removed_map:
            self.data.clear()
            if old_provider and not stale and not account_changed:
                self.data["provider"] = old_provider
            self.match_id = self.local_team = ""
            self.finished = False

        # CS2 switches player IDs while spectating and reports menu activity on disconnect.
        player = section(payload.get("player"))
        old_player = section(self.data.get("player"))
        if player.get("steamid") and player["steamid"] != old_player.get("steamid"):
            self.data.pop("player", None)
        if player.get("activity") == "menu":
            self.data.pop("map", None)
            self.data.pop("round", None)
            self.data.pop("result", None)
            self.data.pop("player", None)
            self.match_id = self.local_team = ""
            self.finished = False

        # Retain known fields for partial updates. Omitted fields named in "previously"
        # are removed when Valve reports that an entire map section disappeared.
        for key in ("provider", "map", "round", "player"):
            if key in payload and not (player.get("activity") == "menu" and key in {"map", "round"}):
                value = payload[key]
                if isinstance(value, dict):
                    merge(self.data.setdefault(key, {}), value)
                elif value is None:
                    self.data.pop(key, None)
        self.received = now

        current_map = section(self.data.get("map"))
        local = section(self.data.get("player"))
        account = section(self.data.get("provider")).get("steamid")
        if not isinstance(account, str) or not account.isascii() or not account.isdecimal() or len(account) != 17:
            return None
        if not STEAM_ID_BASE < int(account) <= STEAM_ID_BASE + 0xFFFFFFFF:
            return None
        if local.get("steamid") != account or local.get("activity") == "menu":
            return None
        team = local.get("team")
        if team not in ("CT", "T"):
            return None
        # A first terminal packet can follow a restart or spectating. Require observed play.
        mode = current_map.get("mode")
        map_name = current_map.get("name")
        if mode not in MATCH_MODES or not map_name:
            return None
        phase = current_map.get("phase")
        if phase == "live" and not self.finished:
            self.match_id = self.match_id or uuid4().hex
            self.local_team = team
        if phase not in GAME_OVER or not self.match_id or self.finished or self.local_team != team:
            return None
        if any(count(section(incoming_map.get(side)).get("score")) is None for side in ("team_ct", "team_t")):
            return None
        ct = count(section(current_map.get("team_ct")).get("score"))
        t = count(section(current_map.get("team_t")).get("score"))
        if ct is None or t is None or ct + t == 0:
            return None
        own, opponent = (ct, t) if team == "CT" else (t, ct)
        outcome = "win" if own > opponent else "loss" if own < opponent else "tie"
        stats = section(local.get("match_stats"))
        return (self.match_id, account, now, map_name, mode, outcome, ct, t,
                count(stats.get("kills")), count(stats.get("deaths")), count(stats.get("assists")))

    def complete(self, outcome: str) -> None:
        self.finished = True
        self.data["result"] = outcome
