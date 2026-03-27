from __future__ import annotations

import json

from abx.performance.performanceReports import build_performance_surface_report


if __name__ == "__main__":
    print(json.dumps(build_performance_surface_report(), indent=2, sort_keys=True))
