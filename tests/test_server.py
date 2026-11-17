from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from email.message import Message
from http.server import ThreadingHTTPServer
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from gsi_state import GameState
from match_history import MatchHistory
from profile_sync import ProfileSync
from providers import LeetifyProvider, http_json, last20, parse_profile, rating_band
from send_test_data import SAMPLE, STEAM_ID
import server

OTHER_ID = str(int(STEAM_ID) - 1)


def detail(match_id, *, kills=26, deaths=8, heads=16, rounds=16, damage=2573, source="matchmaking"):
    return {"id": match_id, "finished_at": f"2026-11-{int(match_id):02}T12:00:00Z", "data_source": source,
            "team_scores": [{"team_number": 2, "score": 3}, {"team_number": 3, "score": 13}],
            "stats": [{"steam64_id": STEAM_ID, "initial_team_number": 3, "total_kills": kills,
                       "total_deaths": deaths, "total_hs_kills": heads, "rounds_count": rounds,
                       "total_damage": damage, "dpr": 160.81}]}


def final_payload():
    payload = deepcopy(SAMPLE)
    payload["map"].update(phase="gameover", round=21, team_ct={"score": 13}, team_t={"score": 8})
    return payload


class SteamTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(server.normalize_steam_id(STEAM_ID), STEAM_ID)
        self.assertEqual(server.normalize_steam_id(f"https://steamcommunity.com/profiles/{STEAM_ID}"), STEAM_ID)
        for value in (None, "76569999999999999", f"junk{STEAM_ID}", int(STEAM_ID)):
            self.assertEqual(server.normalize_steam_id(value), "")

    def test_active_registry_account(self):
        registry = MagicMock()
        registry.QueryValueEx.return_value = (int(STEAM_ID) - server.STEAM_ID_BASE, 4)
        with patch.dict("sys.modules", {"winreg": registry}):
            self.assertEqual(server.active_steam_id(), STEAM_ID)
            registry.QueryValueEx.return_value = (0, 4)
            self.assertEqual(server.active_steam_id(), "")

    def test_vdf_account_switch_and_override(self):
        with tempfile.TemporaryDirectory() as path, patch.object(server, "active_steam_id", return_value=""):
            steam = Path(path)
            (steam / "config").mkdir()
            vdf = steam / "config" / "loginusers.vdf"
            with patch.object(server, "discover_steam_paths", return_value=[steam]), patch.object(server, "GAME", GameState()):
                for first, second in ((STEAM_ID, OTHER_ID), (OTHER_ID, STEAM_ID)):
                    vdf.write_text(f'"users" {{ "{first}" {{ "MostRecent" "1" "Timestamp" "20" }} '
                                   f'"{second}" {{ "MostRecent" "0" "Timestamp" "21" }} }}', encoding="utf-8-sig")
                    self.assertEqual(server.detect_steam_id(), first)
                    self.assertEqual(server.get_steam_id({"steam_id": second}), second)


class ProviderTests(unittest.TestCase):
    def test_rating_bands(self):
        for value, band in ((None, "unrated"), (4999, "grey"), (5000, "lightblue"), (10000, "blue"),
                            (15000, "purple"), (20000, "pink"), (25000, "red"), (30000, "gold")):
            self.assertEqual(rating_band(value), band)

    def test_documented_provider_contract(self):
        profile = {"steam64_id": STEAM_ID, "name": "Astra", "privacy_mode": "public", "ranks": {"premier": 19309}}
        matches = [detail("15"), detail("15"), detail("16", source="faceit")]
        with patch("providers.http_json", side_effect=[profile, matches]) as http:
            parsed = LeetifyProvider().fetch(STEAM_ID)
        self.assertEqual([call.args[0].split(".com")[1] for call in http.call_args_list],
                         [f"/v3/profile?steam64_id={STEAM_ID}", f"/v3/profile/matches?steam64_id={STEAM_ID}"])
        self.assertEqual(parsed["steam_id"], STEAM_ID)
        self.assertEqual(parsed["premier_rating"], 19309)
        self.assertEqual(parsed["recent_form"], [{"result": "W"}])
        self.assertEqual(parsed["last20"], {"kd": 3.25, "kr": 1.62, "adr": 160.8,
                                           "avg_kills": 26.0, "hs_percent": 61.5,
                                           "win_percent": 100.0, "match_count": 1, "matches_with_stats": 1})

    def test_coverage_uses_per_metric_denominators_and_unknown_results(self):
        profile = {"ranks": {"faceit_elo": 2000}, "recent_matches": [
            {"id": "17", "finished_at": "2026-11-17T12:00:00Z", "data_source": "matchmaking", "outcome": "loss"},
            {"id": "18", "finished_at": "2026-11-18T12:00:00Z", "data_source": "faceit", "outcome": "win"},
        ]}
        parsed = parse_profile(profile, STEAM_ID, [detail("15"), detail("16", kills=40, heads=None, deaths=None,
                                                                       rounds=None, damage=None)])
        self.assertIsNone(parsed["premier_rating"])
        self.assertEqual(parsed["last20"]["kd"], 3.25)
        self.assertEqual(parsed["last20"]["kr"], 1.62)
        self.assertEqual(parsed["last20"]["hs_percent"], 61.5)
        self.assertEqual(parsed["last20"]["avg_kills"], 33)
        self.assertEqual([row["result"] for row in parsed["recent_form"]], ["L", "W", "W"])
        stats, form = last20([{"kills": 5, "deaths": 0, "headshots": None}])
        self.assertIsNone(stats["kd"])
        self.assertIsNone(stats["win_percent"])
        self.assertEqual(form, [{"result": "?"}])

    def test_retry_cache_rating_delta_and_account_isolation(self):
        provider = MagicMock()
        verified = parse_profile({"ranks": {"premier": 19309}}, STEAM_ID)
        verified.update(match_details=True)
        higher = {**verified, "premier_rating": 19560}
        provider.fetch.side_effect = [verified, URLError("offline"), higher,
                                      HTTPError("https://leetify.com", 404, "", None, None)]
        sync = ProfileSync(provider)
        self.assertIsNone(sync.step(STEAM_ID, 1000)["rating_change"])
        self.assertEqual(sync.step(STEAM_ID, 1600)["status"], "cached")
        self.assertEqual(sync.step(STEAM_ID, 1659, forced=True)["updated_at"], 1000)
        self.assertEqual(provider.fetch.call_count, 2)
        self.assertEqual(sync.step(STEAM_ID, 1660)["rating_change"], 251)
        self.assertIsNone(sync.step(OTHER_ID, 1661)["premier_rating"])
        self.assertEqual(sync.state["steam_id"], OTHER_ID)

    def test_rate_limit_blocks_forced_sync(self):
        headers = Message()
        headers["Retry-After"] = "240"
        provider = MagicMock()
        provider.fetch.side_effect = HTTPError("https://leetify.com", 429, "", headers, None)
        sync = ProfileSync(provider)
        self.assertEqual(sync.step(STEAM_ID, 100)["status"], "unavailable")
        sync.step(STEAM_ID, 339, forced=True)
        self.assertEqual(provider.fetch.call_count, 1)
        sync.step(STEAM_ID, 340)
        self.assertEqual(provider.fetch.call_count, 2)

    def test_match_endpoint_failure_keeps_previous_verified_history(self):
        profile = {"steam64_id": STEAM_ID, "privacy_mode": "public", "ranks": {"premier": 19309}}
        for failure in (TimeoutError(), {"unexpected": []}):
            with self.subTest(failure=failure), patch("providers.http_json", side_effect=[
                profile, [detail("15")], profile, failure,
            ]):
                sync = ProfileSync(LeetifyProvider())
                first = sync.step(STEAM_ID, 1000)
                second = sync.step(STEAM_ID, 1600)
                self.assertEqual(second["status"], "partial")
                self.assertEqual(second["last20"], first["last20"])
                self.assertEqual(second["recent_form"], first["recent_form"])

    def test_api_key_is_only_sent_on_initial_request(self):
        with patch("providers.urlopen") as open_url:
            open_url.return_value.__enter__.return_value.read.return_value = b"{}"
            http_json("https://example.com/profile", "fictional-test-key")
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer fictional-test-key")
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual(open_url.call_args.kwargs["timeout"], 8)

    def test_verified_missing_rating_clears_previous_rating(self):
        profile = {"steam64_id": STEAM_ID, "privacy_mode": "public", "ranks": {"premier": 19309}}
        unrated = {**profile, "ranks": {"premier": None, "faceit_elo": 3000}}
        with patch("providers.http_json", side_effect=[profile, [], unrated, []]):
            sync = ProfileSync(LeetifyProvider())
            self.assertEqual(sync.step(STEAM_ID, 1000)["premier_rating"], 19309)
            self.assertIsNone(sync.step(STEAM_ID, 1600)["premier_rating"])


class GsiTests(unittest.TestCase):
    def test_supported_modes_and_draws(self):
        for mode in ("premier", "competitive", "wingman", "scrimcomp2v2"):
            with self.subTest(mode=mode):
                game = GameState()
                sample = deepcopy(SAMPLE)
                sample["map"]["mode"] = mode
                game.ingest(sample, 100)
                final = final_payload()
                final["map"].update(mode=mode, team_ct={"score": 8}, team_t={"score": 8})
                match = game.ingest(final, 110)
                self.assertEqual(match[4:6], (mode, "tie"))

    def test_partial_final_persistence_and_duplicate_terminal(self):
        game = GameState()
        self.assertIsNone(game.ingest(deepcopy(SAMPLE), 100))
        self.assertIsNone(game.ingest({"map": {"phase": "gameover"}}, 110))
        self.assertNotIn("result", game.data)
        complete = {"map": {"team_ct": {"score": 13}, "team_t": {"score": 8}}}
        match = game.ingest(complete, 111)
        self.assertEqual(match[1:11], (STEAM_ID, 111, "de_mirage", "competitive", "win", 13, 8, 18, 9, 4))
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "matches.sqlite3"
            history = MatchHistory(database)
            self.assertTrue(history.record(match))
            self.assertFalse(history.record(match))
            game.complete(match[5])
            self.assertIsNone(game.ingest(final_payload(), 112))
            self.assertIsNone(game.ingest(deepcopy(SAMPLE), 112))
            self.assertIsNone(game.ingest(final_payload(), 113))
            self.assertIsNone(GameState().ingest(final_payload(), 113))
            self.assertEqual(MatchHistory(database).recent(STEAM_ID)[0]["outcome"], "win")
            self.assertEqual(MatchHistory(database).recent(OTHER_ID), [])
            for index in range(25):
                history.record((f"match{index}", STEAM_ID, 1000 + index, *match[3:]))
            self.assertEqual(len(history.recent(STEAM_ID)), 20)
            self.assertEqual(history.recent(STEAM_ID)[-1]["finished_at"], 1005)

    def test_spectating_expiry_and_match_transition(self):
        game = GameState()
        sample = deepcopy(SAMPLE)
        sample["provider"]["timestamp"] = 90
        game.ingest(sample, 100)
        game.ingest({"provider": {"timestamp": 89}, "player": {"activity": "menu"}}, 105)
        self.assertEqual(game.snapshot(106)["data"]["map"]["name"], "de_mirage")
        game.ingest({"player": {"steamid": OTHER_ID, "team": "T"}}, 106)
        self.assertNotIn("match_stats", game.data["player"])
        ending = final_payload()
        ending["player"]["steamid"] = OTHER_ID
        self.assertIsNone(game.ingest(ending, 108))
        self.assertEqual(game.snapshot(154)["data"], {})
        game.ingest({"map": {"name": "de_nuke", "mode": "wingman", "phase": "warmup"}}, 156)
        self.assertNotIn("player", game.data)
        self.assertEqual(game.data["map"]["name"], "de_nuke")
        game.ingest({"player": {"activity": "menu"}}, 157)
        self.assertNotIn("map", game.data)


class HttpTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = directory.name
        for key, value in {
            "HISTORY": MatchHistory(Path(self.tmp) / "history.sqlite3"),
            "SETTINGS_FILE": Path(self.tmp) / "settings.json", "GAME": GameState(),
            "TEST_GAME": GameState(), "PROFILE_STATE": server.empty_profile(), "LOCAL_HISTORY": {},
            "detect_steam_id": lambda: "",
        }.items():
            fake = patch.object(server, key, value)
            fake.start()
            self.addCleanup(fake.stop)
        http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(http.server_close)
        self.addCleanup(http.shutdown)
        self.base = f"http://127.0.0.1:{http.server_port}"

    def request(self, path, payload=None, headers=None, *, method=None):
        data = json.dumps(payload).encode() if payload is not None else None
        with urlopen(Request(self.base + path, data=data, headers=headers or {}, method=method), timeout=4) as response:
            return response.read()

    def test_endpoints_settings_and_sample_isolation(self):
        self.assertIn(b"LAST 20 MATCHES", self.request("/"))
        self.assertIn(b"Steam", self.request("/settings"))
        self.assertTrue(json.loads(self.request("/api/health"))["ok"])
        self.assertEqual(json.loads(self.request("/api/profile"))["premier_rating"], None)
        self.assertEqual(json.loads(self.request("/api/settings", {"steam_id": STEAM_ID}))["settings"]["steam_id"], STEAM_ID)
        self.assertEqual(json.loads(self.request("/api/settings"))["effective_steam_id"], STEAM_ID)
        self.assertTrue(json.loads(self.request("/api/refresh-profile", {}))["ok"])
        self.request("/gsi/test", SAMPLE)
        self.request("/gsi/test", final_payload())
        self.assertTrue(json.loads(self.request("/api/test-state"))["connected"])
        self.assertFalse(json.loads(self.request("/api/overlay"))["state"]["connected"])
        self.assertEqual(server.HISTORY.recent(STEAM_ID), [])
        self.request("/gsi", SAMPLE)
        self.request("/gsi", final_payload())
        self.request("/gsi", final_payload())
        self.assertEqual(json.loads(self.request("/api/state"))["data"]["result"], "win")
        self.assertEqual(len(server.HISTORY.recent(STEAM_ID)), 1)

    def test_bad_payloads_and_external_origin(self):
        # For header-only rejections, avoid racing Windows socket close against a body upload.
        for method, path, payload, headers, code in (
            ("POST", "/gsi", {}, {}, 403),
            ("POST", "/gsi", {"value": float("nan")}, {}, 400),
            ("POST", "/api/settings", {"steam_id": "bad"}, {}, 400),
            ("POST", "/api/refresh-profile", None, {"Origin": "https://example.com"}, 403),
            ("POST", "/api/stop", None, {}, 403),
            ("GET", "/api/profile", None, {"Host": "example.com"}, 403),
            ("POST", "/api/settings", None, {"Content-Length": str(server.MAX_BODY + 1)}, 400),
            ("POST", "/api/settings", None, {"Sec-Fetch-Site": "cross-site"}, 403),
            ("GET", "/web/../server.py", None, {}, 404),
        ):
            with self.subTest(path=path, headers=headers):
                with self.assertRaises(HTTPError) as error:
                    self.request(path, payload, headers, method=method)
                self.assertEqual(error.exception.code, code)
                error.exception.close()

    def test_stop_endpoint(self):
        result = self.request("/api/stop", headers={"X-Premier-Sync-Control": "stop"}, method="POST")
        self.assertEqual(json.loads(result), {"ok": True})


if __name__ == "__main__":
    unittest.main(verbosity=2)
