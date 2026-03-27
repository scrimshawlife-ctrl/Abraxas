from __future__ import annotations

import json

from abx.uncertainty.calibrationReports import build_calibration_report


if __name__ == "__main__":
    print(json.dumps(build_calibration_report(), indent=2, sort_keys=True))
