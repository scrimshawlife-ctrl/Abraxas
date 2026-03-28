from __future__ import annotations

import json

from abx.outcome.intendedOutcomeReports import build_intended_outcome_report


if __name__ == "__main__":
    print(json.dumps(build_intended_outcome_report(), indent=2, sort_keys=True))
