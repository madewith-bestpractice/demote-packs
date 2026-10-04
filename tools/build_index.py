#!/usr/bin/env python3
"""Build index.json from packs/*.json.

Usage:
  python tools/build_index.py          rewrite index.json
  python tools/build_index.py --check  exit 1 if index.json is out of date

The index lists each pack's metadata, button list and the SHA-256 of its
file. The app downloads a pack from `path` and refuses it if the hash
doesn't match.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.json"
FIRST_PARTY = "Made with Best Practice"


def build() -> str:
    packs = []
    for f in sorted(ROOT.glob("packs/*.json")):
        raw = f.read_bytes()
        p = json.loads(raw)
        packs.append({
            "id": p["id"],
            "version": p["version"],
            "path": f"packs/{f.name}",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "name": p["name"],
            "description": p["description"],
            "vendor": p["vendor"],
            "author": p["author"],
            "firstParty": p["author"] == FIRST_PARTY,
            "icon": p["icon"],
            "engine": p["engine"],
            "network": p["network"],
            "buttons": [
                {"id": b["id"], "label": b["label"], "icon": b["icon"],
                 "asks": bool(b.get("variables"))}
                for b in p["buttons"]
            ],
        })
    return json.dumps({"schema": 1, "packs": packs}, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    text = build()
    if "--check" in argv:
        if not INDEX.exists() or INDEX.read_text() != text:
            print("index.json is out of date. Run: python tools/build_index.py")
            return 1
        print("index.json is up to date.")
        return 0
    INDEX.write_text(text)
    print(f"Wrote index.json ({text.count('\"sha256\"')} packs).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
