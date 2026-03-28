from __future__ import annotations

import json

from abx.operator.interventionReports import build_intervention_report


if __name__ == "__main__":
    print(json.dumps(build_intervention_report(), indent=2, sort_keys=True))
