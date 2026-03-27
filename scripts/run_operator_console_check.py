#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.operator_workflows import run_operator_workflow


def main() -> int:
    ap = argparse.ArgumentParser(description="Smoke-check canonical operator workflows")
    ap.add_argument("scenario_json")
    args = ap.parse_args()
    payload = json.loads(Path(args.scenario_json).read_text(encoding="utf-8"))

    results = {
        "inspect-current-frame": run_operator_workflow("inspect-current-frame", payload),
        "inspect-proof-workflow": run_operator_workflow("inspect-proof-workflow", payload),
        "inspect-portfolio-workflow": run_operator_workflow("inspect-portfolio-workflow", payload),
        "inspect-continuity": run_operator_workflow("inspect-continuity", payload),
    }
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
