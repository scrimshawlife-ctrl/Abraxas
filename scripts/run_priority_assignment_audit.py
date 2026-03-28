from __future__ import annotations

import json

from abx.tradeoff.priorityReports import build_priority_assignment_report


if __name__ == "__main__":
    print(json.dumps(build_priority_assignment_report(), indent=2, sort_keys=True))
