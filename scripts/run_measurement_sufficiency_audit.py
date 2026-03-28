from __future__ import annotations

import json

from abx.observability.sufficiencyReports import build_measurement_sufficiency_report


if __name__ == "__main__":
    print(json.dumps(build_measurement_sufficiency_report(), indent=2, sort_keys=True))
