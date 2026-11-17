# Configuration and statistics

| Setting | How to change it |
| --- | --- |
| Selected Steam account | Open `http://127.0.0.1:3000/settings`. Enter an individual SteamID64, or clear it to restore automatic selection. |
| Leetify key | Get an optional key from the [Leetify developer page](https://leetify.com/app/developer), then add `LEETIFY_API_KEY` as a Windows **user** environment variable. Reopen the launcher afterward. |
| Local-only statistics | From Command Prompt in the project folder, run `run_overlay.bat --offline`. This disables Leetify sync for that process. |
| OBS viewport | Use 640 × 180 in Browser Source properties. Apply the output scale in OBS. |
| GSI endpoint | Use the supplied config. The normal install uses `127.0.0.1:3000/gsi`. |

The server creates `%LOCALAPPDATA%\CS2PremierOverlay` at startup. Settings are saved atomically to `settings.json`; [blank example](../examples/example_config.json). SQLite creates `match_history.sqlite3` as needed. The application logs to its console.

## Provider refresh and metrics

Leetify's public v3 profile and match-history endpoints provide the current Premier Rating and available result/detail rows. Normal refresh is every ten minutes. Temporary failures use retry backoff and may retain a previous result in memory. A private, withdrawn or unavailable profile can leave rating blank. The change beside the rating compares two distinct snapshots in the same server session. Individual result tiles show W, L, T or an unknown result. The season badge is a build-time label.

The overlay filters to recognized matchmaking source values, joins rows by match ID and takes the 20 newest. It calculates K/D from paired kill and death counts, K/R from kills and rounds, ADR as damage per round, average kills per covered match, HS% as headshot kills per kill, and win rate as wins per known result including draws. Coverage can differ by metric. Local GSI history can supply K/D, K/R, average kills and outcomes. GSI history has no headshot or damage coverage.

See [third-party notices](THIRD_PARTY.md) for the API terms review.
