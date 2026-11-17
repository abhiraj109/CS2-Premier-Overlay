# Contributing

1. Fork the GitHub repository after it is public. Clone your fork and create a topic branch with `git switch -c fix/short-description`.
2. Install Python 3.10+ and use the [Windows setup steps](docs/INSTALLATION.md) if working on live behavior. The application and Python tests use the standard library.
3. Read the [architecture guide](docs/ARCHITECTURE.md). Keep changes scoped, follow the existing module and browser conventions, and use fictional fixtures with mock API calls. Avoid committing personal runtime files.
4. From the project root, run `python -m unittest discover -s tests -v` and `python -m compileall -q .`. On Windows run `powershell -NoProfile -ExecutionPolicy Bypass -File tests/windows_scripts.ps1` for installer checks.
5. For UI changes run `node --check web/app.js`, `node --check web/settings.js`, and `node tests/browser_smoke.mjs` with Node 22+ and Chrome. Set `CHROME_PATH` if needed. The runner's default output is `dist/browser-smoke.png`.
6. Write a descriptive commit, such as `fix: preserve local match history on retry`. Push to your fork and open a pull request with reproduction steps, test evidence and a labeled demo screenshot for visual changes.

Read the [code of conduct](CODE_OF_CONDUCT.md). Send security disclosures through the private route in [SECURITY.md](SECURITY.md).
