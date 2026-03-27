#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.governance.pruning_audit import pruning_audit_report


if __name__ == "__main__":
    print(json.dumps(pruning_audit_report(REPO_ROOT), indent=2, sort_keys=True))
