from __future__ import annotations

import json

from abx.continuity.planReports import build_long_horizon_plan_report


if __name__ == "__main__":
    print(json.dumps(build_long_horizon_plan_report(), indent=2, sort_keys=True))
