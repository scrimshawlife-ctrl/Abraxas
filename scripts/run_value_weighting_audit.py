from __future__ import annotations

import json

from abx.tradeoff.weightingReports import build_value_weighting_report


if __name__ == "__main__":
    print(json.dumps(build_value_weighting_report(), indent=2, sort_keys=True))
