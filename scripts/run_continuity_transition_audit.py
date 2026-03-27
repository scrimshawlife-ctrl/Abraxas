from __future__ import annotations

import json

from abx.continuity.transitionReports import build_continuity_transition_report


if __name__ == "__main__":
    print(json.dumps(build_continuity_transition_report(), indent=2, sort_keys=True))
