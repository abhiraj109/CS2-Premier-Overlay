"""Refresh the selected profile in the background and keep transient data in memory."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import logging
import time
from urllib.error import HTTPError, URLError

from providers import PrivateProfile, last20

REFRESH_SECONDS = 600
log = logging.getLogger("premier-overlay")


def empty_profile(steam_id: str = "", status: str = "starting", error: str = "") -> dict:
    stats, form = last20([])
    return {"steam_id": steam_id, "status": status, "error": error, "name": "", "avatar": "",
            "premier_rating": None, "rating_band": "unrated", "rating_change": None,
            "last20": stats, "recent_form": form, "updated_at": None, "source": ""}


def retry_delay(value: str | None) -> float:
    if value:
        try:
            delay = int(value)
        except ValueError:
            try:
                delay = (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                delay = REFRESH_SECONDS
        return max(60, delay)
    return REFRESH_SECONDS


class ProfileSync:
    def __init__(self, provider):
        self.provider = provider
        self.state = empty_profile()
        self.due = 0.0
        self.last_attempt = 0.0
        self.blocked_until = 0.0
        self.failures = 0

    def step(self, steam_id: str, now: float, forced: bool = False) -> dict:
        if steam_id != self.state["steam_id"]:
            self.state = empty_profile(steam_id, "syncing")
            self.due = 0.0
            self.last_attempt = 0.0
            self.failures = 0
        if not steam_id:
            self.state = empty_profile(status="setup", error="Open Steam or set SteamID64 in Settings.")
            return self.state
        if self.blocked_until > now:
            if self.state["status"] == "syncing":
                self.state = empty_profile(steam_id, "unavailable", "Leetify rate limit. Retry scheduled.")
            return self.state
        if now < self.due and (not forced or self.failures or now < self.last_attempt + 60):
            return self.state

        previous = self.state
        self.last_attempt = now
        self.due = now + REFRESH_SECONDS
        try:
            result = self.provider.fetch(steam_id)
        except (HTTPError, URLError, OSError, ValueError) as exc:
            code = exc.code if isinstance(exc, HTTPError) else None
            if isinstance(exc, PrivateProfile) or code in (403, 404, 410):
                message = "Public Leetify profile unavailable for this Steam account."
                self.state = empty_profile(steam_id, "unavailable", message)
            elif code == 401:
                self.state = empty_profile(steam_id, "unavailable", "Check the optional Leetify API key.")
            else:
                self.failures += 1
                if code == 429:
                    self.blocked_until = now + retry_delay(exc.headers.get("Retry-After") if exc.headers else None)
                    self.due = self.blocked_until
                    message = "Leetify rate limit. Retry scheduled."
                else:
                    self.due = now + min(REFRESH_SECONDS, 60 * 2 ** min(self.failures - 1, 4))
                    message = f"Leetify sync failed ({code or type(exc).__name__}). Retry scheduled."
                status = "cached" if previous["updated_at"] else "unavailable"
                self.state = {**previous, "status": status, "error": message}
            log.warning(self.state["error"])
            if isinstance(exc, HTTPError):
                exc.close()
            return self.state

        self.failures = 0
        retry_after = result.pop("retry_after", None)
        if retry_after is not None:
            # Provider history can be rate-limited while the profile call succeeds.
            self.blocked_until = now + retry_delay(retry_after)
            self.due = self.blocked_until
        history_error = result.pop("history_error", "")
        rating = result["premier_rating"]
        old_rating = previous["premier_rating"]
        delta = previous["rating_change"] if rating is not None and rating == old_rating else None
        if rating is not None and old_rating is not None and rating != old_rating:
            delta = rating - old_rating
        if not result["match_details"] and previous.get("match_details"):
            for key in ("last20", "recent_form", "match_details"):
                result[key] = previous[key]
        self.state = {**result, "status": "partial" if history_error or rating is None else "online",
                      "updated_at": now, "rating_change": delta,
                      "error": history_error or ("Premier Rating unavailable." if rating is None else "")}
        if history_error:
            log.warning("%s", history_error)
        return self.state
