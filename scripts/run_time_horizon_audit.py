from __future__ import annotations

import json

from abx.freshness.horizonReports import build_time_horizon_report


if __name__ == "__main__":
    print(json.dumps(build_time_horizon_report(), indent=2, sort_keys=True))
