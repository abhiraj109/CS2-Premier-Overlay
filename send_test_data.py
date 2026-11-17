"""Send sample gameplay to the isolated GSI preview route."""

import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from server import HOST, PORT

SAMPLE = json.loads((Path(__file__).resolve().parent / "examples" / "sample_gsi_payload.json").read_text(encoding="utf-8"))
STEAM_ID = SAMPLE["provider"]["steamid"]


def main() -> None:
    base = f"http://{HOST}:{PORT}"
    request = Request(f"{base}/gsi/test", data=json.dumps(SAMPLE).encode("utf-8"),
                      headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=3) as response:
            json.load(response)
    except (OSError, URLError, ValueError) as exc:
        raise SystemExit(f"Could not send sample data. Start run_overlay.bat first. ({exc})")
    print(f"Sample received. Preview it at {base}/?gsi-test=1 for the next 45 seconds.")
    print("Use /?demo=1 for a persistent sample with example rating and statistics.")


if __name__ == "__main__":
    main()
