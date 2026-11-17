"""Build a Windows ZIP from an explicit list of public files."""

from hashlib import sha256
from pathlib import Path
import re
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
FILES = """
README.md VERSION CHANGELOG.md SECURITY.md
server.py gsi_state.py match_history.py providers.py profile_sync.py send_test_data.py
setup_once.bat run_overlay.bat stop_overlay.bat send_test_data.bat run_tests.bat
install_gsi.bat install_gsi.ps1 uninstall_gsi.bat uninstall_gsi.ps1
install_startup.bat install_startup.ps1 remove_startup.bat uninstall_startup.ps1
gsi/gamestate_integration_cs2_obs_overlay.cfg
examples/example_config.json examples/sample_gsi_payload.json
web/index.html web/app.js web/styles.css web/settings.html web/settings.js web/settings.css web/leetify-attribution.png
assets/screenshots/preview.png
docs/INSTALLATION.md docs/CONFIGURATION.md docs/TROUBLESHOOTING.md docs/FAQ.md
docs/ARCHITECTURE.md docs/API.md docs/THIRD_PARTY.md docs/LICENSING.md docs/PUBLISHING.md docs/RELEASE_NOTES.md
CONTRIBUTING.md CODE_OF_CONDUCT.md docs/TEST_RESULTS.md
tests/test_server.py tests/browser_smoke.mjs tests/windows_scripts.ps1 scripts/build_release.py
""".split()


def main() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise SystemExit("VERSION must be in major.minor.patch form.")
    licensed = (ROOT / "LICENSE").is_file()
    files = sorted([*FILES, "LICENSE"] if licensed else FILES)
    name = f"CS2-Premier-Overlay-{version}"
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / f"{name}-windows{'-candidate' if not licensed else ''}.zip"
    with tempfile.TemporaryDirectory(dir=dist) as temporary:
        staged = Path(temporary) / archive.name
        with ZipFile(staged, "w") as output:
            for path in files:
                content = (ROOT / path).read_bytes()
                if path.endswith((".bat", ".ps1")):
                    content = content.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
                output.writestr(ZipInfo(f"{name}/{path}"), content, compress_type=ZIP_DEFLATED)
        with ZipFile(staged) as output:
            if output.testzip() is not None or output.namelist() != [f"{name}/{path}" for path in files]:
                raise SystemExit("Release ZIP verification failed.")
        staged.replace(archive)
    print(f"{archive.name}  SHA-256 {sha256(archive.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
