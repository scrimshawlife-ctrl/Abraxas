from __future__ import annotations

import json

from abx.explanation.explanationScorecard import build_explanation_governance_scorecard
from abx.explanation.explanationScorecardSerialization import serialize_explanation_scorecard


if __name__ == "__main__":
    scorecard = build_explanation_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_explanation_scorecard(scorecard))}, indent=2, sort_keys=True))
