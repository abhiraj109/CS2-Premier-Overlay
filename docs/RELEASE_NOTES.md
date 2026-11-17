# CS2 Premier Sync for OBS 4.1.0

This first release packages a 640 × 180 Browser Source with Steam account detection, CS2 GSI, Premier Rating and recent matchmaking stats through Leetify, and SQLite fallback history.

**Requirements** Windows 10 or 11, Python 3.10+, and OBS Studio. Install Steam and CS2 for live GSI. A public Leetify profile linked to the same Steam account supplies online stats.

**Install** Extract the Windows ZIP, run `setup_once.bat`, start `run_overlay.bat`, and restart CS2. In OBS add a Browser Source at `http://127.0.0.1:3000/` with width 640 and height 180. Visit `http://127.0.0.1:3000/?demo=1` to preview labeled sample data. See the [installation guide](INSTALLATION.md).

**Limitations** GSI may label Premier and Competitive as Matchmaking and reports Wingman when identifiable. Local history requires observed play and a usable final score. ADR and headshot percentage require provider detail. Rating change compares snapshots in the same session. Settings and history live in Local AppData. See [configuration and coverage](CONFIGURATION.md).
