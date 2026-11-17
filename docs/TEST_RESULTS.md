# Windows verification

Release candidate 4.1.0, tested November 17, 2026 on Windows 11 25H2. Tests used synthetic accounts and mock Leetify responses.

| Check | Result |
| --- | --- |
| Python and JavaScript | Python 3.10-compatible syntax and JavaScript syntax passed. Isolated import confirmed the server and its SQLite/TLS dependencies use the Python standard library. |
| Python test suite | 17 passed on CPython 3.10.21, 3.14.7 and 3.15.2 on Windows. Tests covered Steam discovery, provider parsing and retry behavior, GSI transitions, per-account SQLite history, and real loopback HTTP. |
| Local request boundaries | Tests passed for invalid hosts and origins, cross-site requests, malformed and oversized JSON, GSI token enforcement, source directory traversal protection and the stop route. The API key is sent on the initial provider request only. |
| Browser Source page | Chrome rendered a 640 × 180 viewport at DPR 1 and 2. The demo PNG has transparent corners and no scrollbar or scaling transform. Smoke checks covered the sample label, six metrics, five result tiles, empty live state, sample GSI and Settings. Browser simulations matched the OBS scaling examples at 1080p, 1440p and 4K. |
| Windows setup scripts | PowerShell scripts parsed successfully. GSI install and removal worked against an isolated Steam library with spaces in its path. Startup shortcut creation, target and removal worked under temporary AppData. The one-time setup batch succeeded with a Steam fixture and returned an error for a missing library. The standalone GSI and Startup batch wrappers also passed. |
| Extracted candidate ZIP | CRC and a normal Windows extraction passed. From an extracted path containing spaces, the launch, sample-data, stop and test batch files passed. A synthetic completed match and temporary settings persisted in Local AppData across a stop and restart. |
| GitHub workflow and documentation | The GitHub Actions workflow passed actionlint. Relative documentation links and anchors were checked, and the external linked pages responded. Hosted CI will run on GitHub after publication. |
| Privacy and provenance | Gitleaks reported no detected secrets in the candidate source. Manual review checked identifiers, external URLs, sample data and the packaged files. The bundled Leetify PNG matched the official White Small artwork byte for byte. The local repo had no commits to scan. |

The portable OBS test stalled during startup on this host. Browser rendering and scaling were verified in Chrome. A fresh render in OBS, live CS2 matchmaking GSI, Windows 10 specifically and a successful live Leetify account lookup still need verification. The provider terms review is tracked in [third-party notices](THIRD_PARTY.md).
