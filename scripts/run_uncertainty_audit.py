from __future__ import annotations

import json

from abx.uncertainty.uncertaintyReports import build_uncertainty_report


if __name__ == "__main__":
    print(json.dumps(build_uncertainty_report(), indent=2, sort_keys=True))
