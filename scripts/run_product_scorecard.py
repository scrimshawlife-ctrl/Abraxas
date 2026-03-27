from __future__ import annotations

import json

from abx.productization.productScorecard import build_productization_governance_scorecard
from abx.productization.productScorecardSerialization import serialize_productization_scorecard


if __name__ == "__main__":
    scorecard = build_productization_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_productization_scorecard(scorecard))}, indent=2, sort_keys=True))
