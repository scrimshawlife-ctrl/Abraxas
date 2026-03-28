from __future__ import annotations

import json

from abx.tradeoff.transitionReports import build_weighting_transition_report


if __name__ == "__main__":
    print(json.dumps(build_weighting_transition_report(), indent=2, sort_keys=True))
