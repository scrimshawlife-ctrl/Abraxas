from __future__ import annotations

import json

from abx.closure.gapReports import build_residual_gap_report


if __name__ == "__main__":
    print(json.dumps(build_residual_gap_report(), indent=2, sort_keys=True))
