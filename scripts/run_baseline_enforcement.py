#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.governance.baseline_enforcement import run_baseline_enforcement


if __name__ == "__main__":
    result = run_baseline_enforcement(repo_root=REPO_ROOT)
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    raise SystemExit(1 if result.status == "FAIL" else 0)
