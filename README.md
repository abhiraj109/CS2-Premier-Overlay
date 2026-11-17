# CS2 Premier Sync for OBS

A 640 × 180 OBS Browser Source for Windows 10 and 11. Show your CS Rating, recent matchmaking stats, and live Counter-Strike 2 scores in one scene. The preview uses fictional data.

![CS2 Premier Sync banner and overlay preview with sample data](assets/screenshots/preview.png)

## Quick start

1. Install [Python 3.10 or newer](https://www.python.org/downloads/windows/) and [OBS Studio](https://obsproject.com/download). Enable the Python launcher or add Python to PATH.
2. Extract the release ZIP to a permanent folder and run `setup_once.bat` to install the CS2 Game State Integration (GSI) config. The optional Windows Startup shortcut launches this copy of the project.
3. Run `run_overlay.bat` and fully restart CS2. In OBS add a **Browser** source with URL `http://127.0.0.1:3000/`, **Width 640** and **Height 180**. Keep **Local file** off.
4. Open `http://127.0.0.1:3000/?demo=1` to preview fictional data. If you use the demo URL in OBS, restore `http://127.0.0.1:3000/` for live use.

See the [Windows installation guide](docs/INSTALLATION.md) for screenshots, manual GSI install, scaling, updates and uninstall. Use `stop_overlay.bat` to stop the server.

## Feature support

| Feature | Availability | Data source |
| --- | --- | --- |
| Premier Rating | When the public profile has a current CS Rating | Leetify `ranks.premier` |
| Player name | When Steam, the local game or the public profile reports it | Steam login data, GSI, Leetify |
| K/D | Recent recorded matches with kills and deaths | Leetify detail, or GSI history |
| Last 20 matches | Up to 20 available matches; five recent result tiles | Leetify matchmaking, or GSI history |
| Headshot % | When provider matches report headshot kills | Leetify match detail |
| Win rate | When known results are available | Leetify matchmaking, or GSI history |
| ADR | When provider matches include round and damage data | Leetify match detail |
| Live score, map and K/D/A | When CS2 reports them for the selected account | GSI |

Premier and Competitive can both appear as **Matchmaking** when CS2 reports `competitive`. Wingman appears when the feed identifies it. CS Rating applies to Premier. Local history requires the overlay to see the local player during live play and receive a final score. Practice or community matches can report similar mode fields. The overlay uses either provider history or local history for a display, with missing metrics shown as dashes.

Steam detection checks the active Windows Steam account, the live CS2 account, then Steam's recent-login config. Set a one-time override at `http://127.0.0.1:3000/settings`. The normal launcher looks up the selected SteamID64 with Leetify. Launch from Command Prompt with `run_overlay.bat --offline` for GSI and local history without provider requests. The Browser Source can reveal the selected Steam ID, name and avatar during a stream. See [configuration and statistics](docs/CONFIGURATION.md) and [privacy](SECURITY.md).

## Help and development

- [Troubleshooting](docs/TROUBLESHOOTING.md) covers Python, Steam, GSI, Leetify, OBS size and port 3000.
- [FAQ](docs/FAQ.md) answers common setup and data questions.
- [Architecture](docs/ARCHITECTURE.md) and [local API](docs/API.md) describe the server, storage and browser.
- Run `run_tests.bat` on Windows or `python -m unittest discover -s tests -v` from the project root. See [contributing](CONTRIBUTING.md), [test results](docs/TEST_RESULTS.md), and the [changelog](CHANGELOG.md).

## License and attribution

The project code and documentation are released under the [MIT License](LICENSE). See the [third-party notices](docs/THIRD_PARTY.md) for the Leetify attribution artwork and provider terms. This is an independent community project with no affiliation with Valve, Steam, FACEIT, Leetify or OBS Studio. Their names and marks belong to their respective owners.
