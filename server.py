from __future__ import annotations

import argparse
import copy
import json
import logging
from math import isfinite
import mimetypes
import os
from pathlib import Path
import re
import sqlite3
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from gsi_state import GameState, STEAM_ID_BASE, section
from match_history import MatchHistory
from profile_sync import REFRESH_SECONDS, ProfileSync, empty_profile
from providers import LeetifyProvider, last20

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DATA_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share") / "CS2PremierOverlay"
SETTINGS_FILE = DATA_DIR / "settings.json"
HISTORY = MatchHistory(DATA_DIR / "match_history.sqlite3")
HOST = "127.0.0.1"
PORT = 3000
GSI_TOKEN = "cs2-premier-obs-local"
MAX_BODY = 64 * 1024

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("premier-overlay")
GAME = GameState()
TEST_GAME = GameState()
STATE_LOCK = threading.Lock()
SETTINGS_LOCK = threading.Lock()
PROFILE_LOCK = threading.Lock()
PROFILE_REFRESH_EVENT = threading.Event()
PROFILE_STATE = empty_profile()
LOCAL_HISTORY: dict = {}
LOCAL_NAME = ""


def load_settings() -> dict[str, Any]:
    try:
        values = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        values = {}
    return {"steam_id": normalize_steam_id(section(values).get("steam_id"))}


def normalize_steam_id(raw: Any) -> str:
    if not isinstance(raw, str):
        return ""
    match = re.fullmatch(r"(?:https://steamcommunity\.com/profiles/)?([0-9]{17})/?", raw.strip())
    if match and STEAM_ID_BASE < int(match[1]) <= STEAM_ID_BASE + 0xFFFFFFFF:
        return match[1]
    return ""


def save_settings(values: dict[str, Any]) -> dict[str, Any]:
    raw = values.get("steam_id")
    steam_id = normalize_steam_id(raw)
    if raw != "" and not steam_id:
        raise ValueError("Enter a valid SteamID64 or clear the field for automatic detection.")
    cleaned = {"steam_id": steam_id}
    with SETTINGS_LOCK:
        temporary = SETTINGS_FILE.with_suffix(".tmp")
        temporary.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
        temporary.replace(SETTINGS_FILE)
    PROFILE_REFRESH_EVENT.set()
    return cleaned


def finite_float(value: str) -> float:
    result = float(value)
    if not isfinite(result):
        raise ValueError("Non-finite JSON number")
    return result


def discover_steam_paths() -> list[Path]:
    paths: list[Path] = []
    try:
        import winreg  # type: ignore
        for root, subkey in (
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
        ):
            try:
                with winreg.OpenKey(root, subkey) as key:
                    for value_name in ("SteamPath", "InstallPath"):
                        try:
                            value, _ = winreg.QueryValueEx(key, value_name)
                            if value:
                                paths.append(Path(os.path.expandvars(str(value))))
                        except OSError:
                            pass
            except OSError:
                pass
    except ImportError:
        pass

    for env in (os.environ.get("PROGRAMFILES(X86)"), os.environ.get("PROGRAMFILES")):
        if env:
            paths.append(Path(env) / "Steam")
    paths.extend((Path("C:/Program Files (x86)/Steam"), Path("C:/Program Files/Steam")))

    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def active_steam_id() -> str:
    """Read Steam's active numeric account ID from its Windows registry key."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess") as key:
            account, _ = winreg.QueryValueEx(key, "ActiveUser")
        if type(account) is int and 0 < account <= 0xFFFFFFFF:
            return str(STEAM_ID_BASE + account)
    except (ImportError, OSError):
        pass
    return ""


def login_users() -> Iterator[list[tuple[bool, int, str, str]]]:
    pattern = re.compile(r'"(\d{17})"\s*\{([^{}]*)\}', re.S)
    for steam_path in discover_steam_paths():
        try:
            text = (steam_path / "config" / "loginusers.vdf").read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            continue
        candidates = []
        for match in pattern.finditer(text):
            steam_id = normalize_steam_id(match[1])
            if steam_id:
                recent = bool(re.search(r'"MostRecent"\s*"1"', match[2], re.I))
                stamp = re.search(r'"Timestamp"\s*"(\d{1,16})"', match[2], re.I)
                persona = re.search(r'"PersonaName"\s*"((?:\\.|[^"\\])*)"', match[2], re.I)
                name = re.sub(r'\\(["\\])', r'\1', persona[1])[:80] if persona else ""
                candidates.append((recent, int(stamp[1]) if stamp else 0, steam_id, name))
        if candidates:
            yield candidates


def detect_steam_id() -> str:
    active = active_steam_id()
    if active:
        return active
    with STATE_LOCK:
        live = GAME.snapshot(time.time())["data"]
        account = normalize_steam_id(section(live.get("provider")).get("steamid"))
    if account:
        return account
    for candidates in login_users():
        recent, stamp, steam_id, _ = max(candidates)
        if recent or stamp or len(candidates) == 1:
            return steam_id
    return ""


def get_steam_id(settings: dict | None = None) -> str:
    if settings is None:
        settings = load_settings()
    return settings["steam_id"] or detect_steam_id()


def local_history(steam_id: str) -> dict:
    try:
        rows = HISTORY.recent(steam_id) if steam_id else []
    except sqlite3.Error:
        log.exception("Could not read local match history")
        rows = []
    for row in rows:
        row["rounds"] = row["ct_score"] + row["t_score"]
    stats, form = last20(rows)
    return {"last20": stats, "recent_form": form, "history_source": "local",
            "history_updated_at": rows[0]["finished_at"] if rows else None}


def profile_worker(offline: bool = False) -> None:
    global PROFILE_STATE, LOCAL_HISTORY, LOCAL_NAME
    sync = None if offline else ProfileSync(LeetifyProvider())
    selected = None
    while True:
        steam_id = get_steam_id()
        forced = PROFILE_REFRESH_EVENT.is_set()
        PROFILE_REFRESH_EVENT.clear()
        if steam_id != selected:
            name = next((name for group in login_users() for _, _, account, name in group
                         if name and account == steam_id), "") if steam_id else ""
            with PROFILE_LOCK:
                PROFILE_STATE = empty_profile(steam_id, "syncing")
                LOCAL_HISTORY = local_history(steam_id)
                LOCAL_NAME = name
            selected = steam_id
        result = (sync.step(steam_id, time.time(), forced) if sync else
                  empty_profile(steam_id, "offline", "Leetify sync disabled for this session."))
        if get_steam_id() == steam_id:
            with PROFILE_LOCK:
                PROFILE_STATE = result
        PROFILE_REFRESH_EVENT.wait(5)


def profile_snapshot() -> dict:
    with PROFILE_LOCK:
        profile = PROFILE_STATE.copy()
        profile["name"] = profile["name"] or LOCAL_NAME
        if not profile["last20"]["match_count"] and LOCAL_HISTORY.get("last20", {}).get("match_count"):
            profile.update(LOCAL_HISTORY)
        elif profile["last20"]["match_count"]:
            profile["history_source"] = "leetify"
        return profile


def send_json(handler: BaseHTTPRequestHandler, data: Any, status: int = 200) -> None:
    raw = json.dumps(data, ensure_ascii=True, allow_nan=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(raw)


class Handler(BaseHTTPRequestHandler):
    server_version = "RoundframeForCS2"
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(6)

    def log_message(self, fmt: str, *args: Any) -> None:
        log.debug(fmt, *args)

    def is_local(self) -> bool:
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        origin = self.headers.get("Origin")
        return self.headers.get("Host") in hosts and (
            origin is None or origin in {f"http://{host}" for host in hosts}
        ) and self.headers.get("Sec-Fetch-Site") != "cross-site"

    def _read_json(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_BODY:
                return None
            value = json.loads(self.rfile.read(length), parse_float=finite_float, parse_constant=finite_float)
            return value if isinstance(value, dict) else None
        except (ValueError, RecursionError, OSError):
            return None

    def do_GET(self) -> None:
        if not self.is_local():
            return send_json(self, {"error": "Local requests only"}, 403)
        url = urlparse(self.path)
        path = url.path
        if path in ("/", "/index.html", "/settings"):
            return self._serve_file(WEB / ("settings.html" if path == "/settings" else "index.html"))
        if path in ("/api/state", "/api/overlay", "/api/test-state", "/api/health"):
            with STATE_LOCK:
                game = TEST_GAME if path == "/api/test-state" else GAME
                state = copy.deepcopy(game.snapshot(time.time()))
            if path in ("/api/state", "/api/test-state"):
                return send_json(self, state)
            profile = profile_snapshot()
            if path == "/api/overlay":
                return send_json(self, {"profile": profile, "state": state})
            return send_json(self, {"ok": True, "gsi_received": bool(state["received_at"]),
                                    "gsi_age_seconds": state["age_seconds"], "gsi_connected": state["connected"],
                                    "profile_status": profile["status"], "steam_detected": bool(profile["steam_id"]),
                                    "profile_refresh_seconds": REFRESH_SECONDS})
        if path == "/api/profile":
            return send_json(self, profile_snapshot())
        if path == "/api/settings":
            settings = load_settings()
            detected = detect_steam_id()
            settings.update(detected_steam_id=detected, effective_steam_id=settings["steam_id"] or detected,
                            using_auto_detect=not bool(settings["steam_id"]))
            return send_json(self, settings)
        if path.startswith("/web/"):
            try:
                candidate = (WEB / path.removeprefix("/web/")).resolve()
                if WEB not in candidate.parents:
                    return send_json(self, {"error": "Not found"}, 404)
                return self._serve_file(candidate)
            except (OSError, ValueError):
                return send_json(self, {"error": "Not found"}, 404)
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        return send_json(self, {"error": "Not found"}, 404)

    def _serve_file(self, path: Path) -> None:
        if not path.is_file():
            return send_json(self, {"error": "File not found"}, 404)
        body = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/javascript":
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        global LOCAL_HISTORY
        if not self.is_local():
            return send_json(self, {"error": "Local requests only"}, 403)
        path = urlparse(self.path).path
        if path == "/api/stop":
            if self.headers.get("X-Premier-Sync-Control") != "stop":
                return send_json(self, {"error": "Use stop_overlay.bat"}, 403)
            send_json(self, {"ok": True})
            self.server.shutdown()
            return
        if path not in ("/api/settings", "/api/refresh-profile", "/gsi", "/gsi/test"):
            return send_json(self, {"error": "Not found"}, 404)
        payload = self._read_json()
        if payload is None:
            return send_json(self, {"error": "Expected a JSON object (maximum 64 KB)"}, 400)
        if path == "/api/settings":
            try:
                return send_json(self, {"ok": True, "settings": save_settings(payload)})
            except ValueError as exc:
                return send_json(self, {"error": str(exc)}, 400)
            except OSError:
                log.exception("Could not save settings")
                return send_json(self, {"error": "Could not save settings"}, 500)
        if path == "/api/refresh-profile":
            PROFILE_REFRESH_EVENT.set()
            return send_json(self, {"ok": True})
        if section(payload.get("auth")).get("token") != GSI_TOKEN:
            return send_json(self, {"error": "Invalid GSI token"}, 403)

        game = TEST_GAME if path == "/gsi/test" else GAME
        with STATE_LOCK:
            try:
                match = game.ingest(payload, time.time())
                if match and game is GAME:
                    HISTORY.record(match)
                if match:
                    game.complete(match[5])
            except sqlite3.Error:
                log.exception("Could not record completed match")
                return send_json(self, {"error": "Could not record completed match"}, 503)
            except (TypeError, ValueError, RecursionError):
                return send_json(self, {"error": "Invalid GSI fields"}, 400)
        if match and game is GAME:
            with PROFILE_LOCK:
                if PROFILE_STATE["steam_id"] == match[1]:
                    LOCAL_HISTORY = local_history(match[1])
        return send_json(self, {"ok": True})


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local CS2 OBS overlay.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--stop", action="store_true", help="stop the running overlay")
    mode.add_argument("--offline", action="store_true", help="disable Leetify requests for this session")
    args = parser.parse_args()
    if args.stop:
        request = Request(f"http://{HOST}:{PORT}/api/stop", method="POST",
                          headers={"X-Premier-Sync-Control": "stop"})
        try:
            with urlopen(request, timeout=3) as response:
                if json.load(response) != {"ok": True}:
                    raise ValueError("Unexpected response")
            print("Roundframe for CS2 stopped.")
        except (OSError, ValueError):
            raise SystemExit("Could not stop Roundframe for CS2. Check whether it is running on port 3000.")
        return
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as exc:
        raise SystemExit(f"Could not start on {HOST}:{PORT}. Check for another overlay or app using port 3000. ({exc})")
    with server:
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
        except OSError:
            raise SystemExit("Could not create the per-user CS2PremierOverlay data folder.")
        threading.Thread(target=profile_worker, args=(args.offline,), name="profile-sync", daemon=True).start()
        log.info("OBS Browser Source at http://%s:%s/ (640 × 180). Ctrl+C stops the server.", HOST, PORT)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
