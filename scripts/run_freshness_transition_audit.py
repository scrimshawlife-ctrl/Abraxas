from __future__ import annotations

import json

from abx.freshness.transitionReports import build_freshness_transition_report


if __name__ == "__main__":
    print(json.dumps(build_freshness_transition_report(), indent=2, sort_keys=True))
