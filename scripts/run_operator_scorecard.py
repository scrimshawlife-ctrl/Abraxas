from __future__ import annotations

import json

from abx.operator.operatorScorecard import build_operator_governance_scorecard
from abx.operator.operatorScorecardSerialization import serialize_operator_scorecard


if __name__ == "__main__":
    scorecard = build_operator_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_operator_scorecard(scorecard))}, indent=2, sort_keys=True))
