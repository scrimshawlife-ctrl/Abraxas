from __future__ import annotations

import json

from abx.failure.transitionReports import build_failure_transition_report


if __name__ == "__main__":
    print(json.dumps(build_failure_transition_report(), indent=2, sort_keys=True))
