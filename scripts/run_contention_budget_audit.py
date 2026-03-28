from __future__ import annotations

import json

from abx.capacity.contentionReports import build_contention_budget_report


if __name__ == "__main__":
    print(json.dumps(build_contention_budget_report(), indent=2, sort_keys=True))
