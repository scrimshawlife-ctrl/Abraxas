from __future__ import annotations

import json

from abx.observability.coverageReports import build_observability_coverage_report


if __name__ == "__main__":
    print(json.dumps(build_observability_coverage_report(), indent=2, sort_keys=True))
