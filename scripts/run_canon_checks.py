#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.canon_checks import run_canon_checks


def main() -> int:
    ap = argparse.ArgumentParser(description="Run canon checks for a simulation scenario payload")
    ap.add_argument("scenario_json", help="Path to scenario payload json")
    args = ap.parse_args()

    payload = json.loads(Path(args.scenario_json).read_text(encoding="utf-8"))
    report = run_canon_checks(payload)
    print(json.dumps(report.__dict__, indent=2, sort_keys=True))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
