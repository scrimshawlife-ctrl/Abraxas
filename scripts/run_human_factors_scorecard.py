from __future__ import annotations

import json

from abx.human_factors.humanFactorsScorecard import build_human_factors_scorecard
from abx.human_factors.humanFactorsScorecardSerialization import serialize_human_factors_scorecard


if __name__ == "__main__":
    scorecard = build_human_factors_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_human_factors_scorecard(scorecard))}, indent=2, sort_keys=True))
