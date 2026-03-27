from __future__ import annotations

import json

from abx.concurrency.concurrentReports import build_concurrent_operation_report


if __name__ == "__main__":
    print(json.dumps(build_concurrent_operation_report(), indent=2, sort_keys=True))
