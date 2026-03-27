#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.closure_summary import build_closure_summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Build closure summary artifact from normalized runtime trade ledger")
    ap.add_argument("run_id")
    ap.add_argument("scenario_id")
    ap.add_argument("--base-dir", default=".")
    args = ap.parse_args()

    artifact = build_closure_summary(base_dir=Path(args.base_dir), run_id=args.run_id, scenario_id=args.scenario_id)
    print(json.dumps(artifact.__dict__, indent=2, sort_keys=True))
    return 0 if artifact.status in {"VALID", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
