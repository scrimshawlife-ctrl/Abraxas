from __future__ import annotations

import json

from abx.observability.blindSpotReports import build_blind_spot_report


if __name__ == "__main__":
    print(json.dumps(build_blind_spot_report(), indent=2, sort_keys=True))
