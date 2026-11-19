# Roundframe for CS2 4.1.0

Originally published as CS2 Premier Sync for OBS. The project name has changed; the v4.1.0 Windows archive remains unchanged.

This first release packages a 640 × 180 Browser Source with Steam account detection, CS2 GSI, Premier Rating and recent matchmaking stats through Leetify, and SQLite fallback history.

**Requirements** Windows 10 or 11, Python 3.10+, and OBS Studio. Install Steam and CS2 for live GSI. A public Leetify profile linked to the same Steam account supplies online stats.

**Install** Download the [v4.1.0 Windows ZIP](https://github.com/abhiraj109/cs2-roundframe/releases/download/v4.1.0/CS2-Premier-Overlay-4.1.0-windows.zip), extract it, run `setup_once.bat`, start `run_overlay.bat`, and restart CS2. In OBS add a Browser Source at `http://127.0.0.1:3000/` with width 640 and height 180. Visit `http://127.0.0.1:3000/?demo=1` to preview labeled sample data. See the [installation guide](https://github.com/abhiraj109/cs2-roundframe/blob/main/docs/INSTALLATION.md).

**SHA-256** `b75b54b4fe3b3caeda3dab09e5485ca937f5011a1a92a283baef459cde711901`

**Limitations** GSI may label Premier and Competitive as Matchmaking and reports Wingman when identifiable. Local history requires observed play and a usable final score. ADR and headshot percentage require provider detail. Rating change compares snapshots in the same session. Settings and history live in Local AppData. See [configuration and coverage](https://github.com/abhiraj109/cs2-roundframe/blob/main/docs/CONFIGURATION.md).
