from __future__ import annotations

import json

from abx.performance.timingReports import build_latency_throughput_overhead_report


if __name__ == "__main__":
    print(json.dumps(build_latency_throughput_overhead_report(), indent=2, sort_keys=True))
