#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.operations.incidents import build_rollback_plan, summarize_rollback_execution


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build rollback plan")
    parser.add_argument("--incident-id", default="inc.none")
    args = parser.parse_args()
    plan = build_rollback_plan(args.incident_id)
    summary = summarize_rollback_execution(args.incident_id)
    print(json.dumps({"plan": plan.__dict__ | {"rollback_steps": [x.__dict__ for x in plan.rollback_steps]}, "summary": summary.__dict__}, indent=2, sort_keys=True))
