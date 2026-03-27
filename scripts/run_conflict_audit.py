from __future__ import annotations

import json

from abx.concurrency.conflictReports import build_conflict_report


if __name__ == "__main__":
    print(json.dumps(build_conflict_report(), indent=2, sort_keys=True))
