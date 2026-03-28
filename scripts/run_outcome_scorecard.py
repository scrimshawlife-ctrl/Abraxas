from __future__ import annotations

import json

from abx.outcome.outcomeScorecard import build_outcome_verification_scorecard
from abx.outcome.outcomeScorecardSerialization import serialize_outcome_scorecard


if __name__ == "__main__":
    scorecard = build_outcome_verification_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_outcome_scorecard(scorecard))}, indent=2, sort_keys=True))
