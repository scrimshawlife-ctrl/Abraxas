from __future__ import annotations

import json

from abx.reconcile.conflictReports import build_state_conflict_report


if __name__ == "__main__":
    print(json.dumps(build_state_conflict_report(), indent=2, sort_keys=True))
