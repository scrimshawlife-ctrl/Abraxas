#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.governance.maintenance_cycle import run_maintenance_cycle


if __name__ == "__main__":
    cycle, summary = run_maintenance_cycle(repo_root=REPO_ROOT)
    print(json.dumps({"cycle": cycle.__dict__, "summary": summary.__dict__}, indent=2, sort_keys=True))
