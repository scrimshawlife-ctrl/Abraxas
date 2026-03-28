from __future__ import annotations

import json

from abx.freshness.freshnessReports import build_freshness_decay_report


if __name__ == "__main__":
    print(json.dumps(build_freshness_decay_report(), indent=2, sort_keys=True))
