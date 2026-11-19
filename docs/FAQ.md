# Frequently asked questions

**Does this change the CS2 HUD?** Roundframe renders into an OBS scene or a regular browser. GSI supplies game data over a local connection; the in-game HUD is unchanged.

**Can I use it without Leetify?** Yes. The server can show live CS2 data and track completed matches locally. In Command Prompt use `run_overlay.bat --offline` to prevent provider requests. Premier Rating, ADR and headshot percentage need provider data.

**What is the difference between Leetify data and local data?** Leetify can supply Premier Rating and processed recent matchmaking matches, including ADR and headshot stats when available. Local GSI data is collected only while Roundframe is running and CS2 sends packets; it supplies live match information and can record completed matches, but has no Premier Rating, ADR or headshot coverage.

**Do I need a Leetify API key?** No. Public profile requests work without one but may hit tighter rate limits. An optional `LEETIFY_API_KEY` Windows user environment variable is documented in [configuration](CONFIGURATION.md#leetify-api-key).

**Why do I see Matchmaking while playing Premier?** CS2 can send `competitive` for both Premier and Competitive. The overlay preserves that ambiguity. Wingman appears when the feed identifies it.

**Where are my files and how do I reset them?** Stop the server first. Back up or remove `settings.json` and `match_history.sqlite3` in `%LOCALAPPDATA%\CS2PremierOverlay`. See [installation and migration](INSTALLATION.md#update-migrate-or-uninstall).

**Why is there no rating change on startup?** The delta needs two successful ratings in the current process and measures the difference between distinct snapshots.

**Can I run OBS on another PC?** This build expects CS2, the overlay server and OBS on the same PC because the server listens on IPv4 loopback. The demo can also be viewed in a normal local browser.
