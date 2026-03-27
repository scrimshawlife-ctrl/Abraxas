from __future__ import annotations

import json

from abx.failure.failureScorecard import build_failure_governance_scorecard
from abx.failure.failureScorecardSerialization import serialize_failure_scorecard


if __name__ == "__main__":
    scorecard = build_failure_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_failure_scorecard(scorecard))}, indent=2, sort_keys=True))
