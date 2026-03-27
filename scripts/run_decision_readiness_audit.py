from __future__ import annotations

import json

from abx.evidence.readinessReports import build_readiness_report


if __name__ == "__main__":
    print(json.dumps(build_readiness_report(), indent=2, sort_keys=True))
