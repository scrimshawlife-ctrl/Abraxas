from __future__ import annotations

import json

from abx.innovation.innovationScorecard import build_experimentation_governance_scorecard
from abx.innovation.innovationScorecardSerialization import serialize_experimentation_scorecard


if __name__ == "__main__":
    scorecard = build_experimentation_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_experimentation_scorecard(scorecard))}, indent=2, sort_keys=True))
