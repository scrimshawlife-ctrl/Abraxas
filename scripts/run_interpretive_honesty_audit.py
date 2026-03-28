from __future__ import annotations

import json

from abx.explanation.honestyReports import build_interpretive_honesty_report


if __name__ == "__main__":
    print(json.dumps(build_interpretive_honesty_report(), indent=2, sort_keys=True))
