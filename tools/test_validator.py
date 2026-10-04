#!/usr/bin/env python3
"""Self-test for the validator: tests/valid/* must pass and tests/invalid/*
must fail. Run in CI so a change to the rules can't quietly let bad packs in.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import ROOT, check_pack  # noqa: E402


def main() -> int:
    failures = []
    for f in sorted(ROOT.glob("tests/valid/*.json")):
        if errs := check_pack(f):
            failures.append(f"{f.name} should be valid: {errs}")
    for f in sorted(ROOT.glob("tests/invalid/*.json")):
        if not check_pack(f):
            failures.append(f"{f.name} should be rejected")
    for line in failures:
        print(f"FAIL {line}")
    print("Validator self-test passed." if not failures else f"{len(failures)} failure(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
