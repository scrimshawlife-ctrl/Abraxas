#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.invariance_harness import run_invariance_harness
from abx.operator_console import dispatch_operator_command


def main() -> int:
    ap = argparse.ArgumentParser(description="Run 12-run invariance harness for operator simulation output")
    ap.add_argument("scenario_json", help="Path to scenario payload json")
    ap.add_argument("--runs", type=int, default=12)
    args = ap.parse_args()

    payload = json.loads(Path(args.scenario_json).read_text(encoding="utf-8"))

    result = run_invariance_harness(
        target="operator.run-simulation",
        runs=args.runs,
        producer=lambda: dispatch_operator_command("run-simulation", payload),
    )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0 if result.status == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
