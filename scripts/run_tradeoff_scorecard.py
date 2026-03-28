from __future__ import annotations

import json

from abx.tradeoff.tradeoffScorecard import build_tradeoff_governance_scorecard
from abx.tradeoff.tradeoffScorecardSerialization import serialize_tradeoff_scorecard


if __name__ == "__main__":
    scorecard = build_tradeoff_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_tradeoff_scorecard(scorecard))}, indent=2, sort_keys=True))
