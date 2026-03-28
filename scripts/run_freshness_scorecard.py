from __future__ import annotations

import json

from abx.freshness.freshnessScorecard import build_freshness_governance_scorecard
from abx.freshness.freshnessScorecardSerialization import serialize_freshness_scorecard


if __name__ == "__main__":
    scorecard = build_freshness_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_freshness_scorecard(scorecard))}, indent=2, sort_keys=True))
