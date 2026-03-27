#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.governance.waivers import build_waiver_audit


if __name__ == "__main__":
    print(json.dumps(build_waiver_audit().__dict__, indent=2, sort_keys=True))
