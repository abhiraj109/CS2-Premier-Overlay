# Release audit

## Baseline

The November 17, 2026 inventory found one application, a browser smoke runner, a Python test suite, a preview image and an older verification report. The folder had no Git metadata or remotes. No duplicate implementation, source ZIP, private database, settings file, or log needed removal. A private backup outside the project was checked byte for byte before changes. The 16 baseline tests passed on Windows.

- `run_overlay.bat` calls `server.py`. Its loopback HTTP server serves HTML, CSS and JavaScript, receives CS2 GSI, and hosts Settings.
- `gsi_state.py` tracks one match at a time. `match_history.py` uses SQLite to keep up to 20 completed observations per Steam account.
- `providers.py` parses Leetify v3 responses. `profile_sync.py` handles refreshes, backoff and in-memory snapshots. Steam discovery uses the registry, GSI and Steam's recent-login file.
- The browser renders live map and score, identity, Premier Rating and recent stats. Fixture tests cover Premier, Competitive and Wingman fields. Leetify availability and exact GSI mode labels depend on upstream data.
- Python uses the standard library. Node and Chrome are optional developer tools. OBS, Steam, and CS2 are installed separately. There were no unused package manifests or vendored libraries.

## Findings and changes

| Baseline observation | Release candidate |
| --- | --- |
| Settings and SQLite opened beside the source. | Use per-user Local AppData. The update guide covers moving an older install without replacing newer data. |
| Demo used a plausible public account number. | Use synthetic account fields in fixtures, omit account numbers from sample rendering, and capture a new preview. |
| Malformed Leetify match responses could be treated as verified details. Provider auth could follow a redirect. | Mark malformed detail responses unavailable and send bearer credentials only on the original request. |
| Existing local HTTP checks already included loopback binding, Host/Origin validation, GSI token and a 64 KiB body limit. | Keep these controls and verify limits and sensitive routes against a temporary server. See [Security](../SECURITY.md). |
| Scripts were colocated with their targets and startup shortcuts. | Keep their paths stable and put release tooling in `scripts/`. |
| The old README mixed setup, development and previous test claims. | Add task-specific guides and replace the old verification report with results from this candidate. |
| Public API use has attribution, data retention and metric presentation rules. | Preserve attribution and memory-only caching. Confirm the existing aggregation and polling with Leetify before public release. See [third-party notices](THIRD_PARTY.md). |

## Directory layout

```text
.
├── server.py and four support modules
├── Windows launch, setup, stop and uninstall scripts
├── web/                 Overlay and Settings interface
├── gsi/                 Installable CS2 GSI configuration
├── examples/            Blank settings and synthetic sample GSI
├── tests/               Python, browser and Windows checks
├── scripts/             Release packaging
├── assets/screenshots/  Labeled demo capture
├── docs/                User, developer and release guides
└── .github/             CI and contribution templates
```

The original root preview moved to `assets/screenshots/preview.png` and was replaced with a fresh demo capture. The previous `TEST_RESULTS.md` moved to `docs/TEST_RESULTS.md` and was superseded by current results. The sample GSI payload moved from `send_test_data.py` into `examples/`. The project-root Python cache moved out of the repository after testing.

Files changed in place are `README.md`, `server.py`, `providers.py`, `send_test_data.py`, `run_overlay.bat`, `run_tests.bat`, `send_test_data.bat`, `install_gsi.bat`, `uninstall_gsi.bat`, `install_startup.bat`, `remove_startup.bat`, `web/index.html`, `web/app.js`, `tests/test_server.py` and `tests/browser_smoke.mjs`. The original GSI configuration, storage schema, CSS and existing startup targets remain compatible.
