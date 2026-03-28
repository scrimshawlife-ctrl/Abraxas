from __future__ import annotations

import json

from abx.operator.traceReports import build_traceability_report


if __name__ == "__main__":
    print(json.dumps(build_traceability_report(), indent=2, sort_keys=True))
