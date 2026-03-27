from __future__ import annotations

import json

from abx.continuity.continuityReports import build_mission_continuity_report


if __name__ == "__main__":
    print(json.dumps(build_mission_continuity_report(), indent=2, sort_keys=True))
