from __future__ import annotations

import json

from abx.semantic.semanticScorecard import build_semantic_governance_scorecard
from abx.semantic.semanticScorecardSerialization import serialize_semantic_scorecard


if __name__ == "__main__":
    scorecard = build_semantic_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_semantic_scorecard(scorecard))}, indent=2, sort_keys=True))
