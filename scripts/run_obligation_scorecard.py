from __future__ import annotations

import json

from abx.obligations.obligationScorecard import build_obligation_governance_scorecard
from abx.obligations.obligationScorecardSerialization import serialize_obligation_scorecard


if __name__ == "__main__":
    scorecard = build_obligation_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_obligation_scorecard(scorecard))}, indent=2, sort_keys=True))
