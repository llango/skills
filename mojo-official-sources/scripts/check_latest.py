#!/usr/bin/env python3
"""Check the latest stable and nightly Mojo versions from official sources.

Fetches https://mojolang.org/releases/ and https://mojolang.org/llms.txt and
reports the latest stable / nightly versions plus the current doc version.
Requires only the Python standard library.
"""

import re
import sys
import urllib.request

RELEASES_URL = "https://mojolang.org/releases/"
LLMS_URL = "https://mojolang.org/llms.txt"
TIMEOUT = 30


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "mojo-official-sources/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    errors = []
    try:
        releases = fetch(RELEASES_URL)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"releases: {exc}")
        releases = ""

    try:
        llms = fetch(LLMS_URL)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"llms.txt: {exc}")
        llms = ""

    if not releases and not llms:
        print("Could not reach official sources:", file=sys.stderr)
        for err in errors:
            print(" ", err, file=sys.stderr)
        return 1

    # "mojo==1.0.0" style version markers appear on the releases page.
    # Pre-release markers: "dev" = nightly, "b" = beta.
    versions = sorted(set(re.findall(r"mojo==([\w.\-]+)", releases)), reverse=True)
    nightlies = [v for v in versions if "dev" in v]
    stables = [v for v in versions if "dev" not in v and "b" not in v.lower()]
    print("Mojo latest versions (mojolang.org/releases/)")
    print("  stable :", stables[0] if stables else "(not found)")
    print("  nightly:", nightlies[0] if nightlies else "(not found)")
    print("  all   :", ", ".join(versions))

    # The llms.txt banner usually states the doc version (e.g. "1.0.0").
    banner = re.search(r"(?i)(version|v)[^0-9]{0,4}(\d+\.\d+(?:\.\d+)?)", llms)
    if banner:
        print("  docs version:", banner.group(2))
    print("Sources checked:", RELEASES_URL, "and", LLMS_URL)
    if errors:
        print("Warnings:", "; ".join(errors), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
