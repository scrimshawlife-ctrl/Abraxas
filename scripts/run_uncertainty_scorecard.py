from __future__ import annotations

import json

from abx.uncertainty.uncertaintyScorecard import build_uncertainty_governance_scorecard
from abx.uncertainty.uncertaintyScorecardSerialization import serialize_uncertainty_scorecard


if __name__ == "__main__":
    scorecard = build_uncertainty_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_uncertainty_scorecard(scorecard))}, indent=2, sort_keys=True))
