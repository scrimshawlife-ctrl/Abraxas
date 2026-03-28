from __future__ import annotations

import json

from abx.freshness.stalenessReports import build_staleness_report


if __name__ == "__main__":
    print(json.dumps(build_staleness_report(), indent=2, sort_keys=True))
