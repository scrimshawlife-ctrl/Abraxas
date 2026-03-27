#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.operations.runbooks import validate_runbooks


if __name__ == "__main__":
    report = validate_runbooks()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(1 if report["status"] == "BROKEN" else 0)
