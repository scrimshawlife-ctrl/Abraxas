from __future__ import annotations

import json

from abx.operator.transitionReports import build_operator_transition_report


if __name__ == "__main__":
    print(json.dumps(build_operator_transition_report(), indent=2, sort_keys=True))
