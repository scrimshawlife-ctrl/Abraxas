#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.governance.change_control import build_change_impact_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build change-control request summary")
    parser.add_argument("request_json")
    args = parser.parse_args()
    payload = json.loads(Path(args.request_json).read_text(encoding="utf-8"))
    print(json.dumps(build_change_impact_summary(payload), indent=2, sort_keys=True))
