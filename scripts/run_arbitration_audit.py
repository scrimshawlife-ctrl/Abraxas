from __future__ import annotations

import json

from abx.concurrency.arbitrationReports import build_arbitration_report


if __name__ == "__main__":
    print(json.dumps(build_arbitration_report(), indent=2, sort_keys=True))
