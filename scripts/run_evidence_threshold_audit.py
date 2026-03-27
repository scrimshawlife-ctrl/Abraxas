from __future__ import annotations

import json

from abx.evidence.thresholdReports import build_threshold_report


if __name__ == "__main__":
    print(json.dumps(build_threshold_report(), indent=2, sort_keys=True))
