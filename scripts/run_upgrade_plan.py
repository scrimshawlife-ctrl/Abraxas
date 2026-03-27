#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.governance.upgrade_plan import build_governed_upgrade_plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build governed upgrade plan")
    parser.add_argument("--baseline-to", default="ABX-GOV-BASELINE-002")
    parser.add_argument("--target-version", default="v1.1.0-rc0")
    args = parser.parse_args()
    payload = {"baseline_to": args.baseline_to, "target_version": args.target_version}
    print(json.dumps(build_governed_upgrade_plan(payload).__dict__, indent=2, sort_keys=True))
