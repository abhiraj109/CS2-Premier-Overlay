# Frequently asked questions

**Does this change the CS2 HUD?** It only renders into an OBS scene or a regular browser. GSI supplies data over a local connection.

**Can I use it without Leetify?** Yes. The server can show live CS2 data and track completed matches locally. In Command Prompt use `run_overlay.bat --offline` to prevent provider requests. Premier Rating, ADR and headshot percentage need provider data.

**Why do I see Matchmaking while playing Premier?** CS2 can send `competitive` for both Premier and Competitive. The overlay preserves that ambiguity. Wingman appears when the feed identifies it.

**Where are my files and how do I reset them?** Stop the server first. Back up or remove `settings.json` and `match_history.sqlite3` in `%LOCALAPPDATA%\CS2PremierOverlay`. See [installation and migration](INSTALLATION.md#update-migrate-or-uninstall).

**Why is there no rating change on startup?** The delta needs two successful ratings in the current process and measures the difference between distinct snapshots.

**Can I run OBS on another PC?** This build expects CS2, the overlay server and OBS on the same PC because the server listens on IPv4 loopback. The demo can also be viewed in a normal local browser.
