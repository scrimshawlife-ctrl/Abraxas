from __future__ import annotations

import json

from abx.agency.actionBoundaryReports import build_action_boundary_report


if __name__ == "__main__":
    print(json.dumps(build_action_boundary_report(), indent=2, sort_keys=True))
