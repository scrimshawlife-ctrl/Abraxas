from __future__ import annotations

import json

from abx.explanation.transitionReports import build_explanation_transition_report


if __name__ == "__main__":
    print(json.dumps(build_explanation_transition_report(), indent=2, sort_keys=True))
