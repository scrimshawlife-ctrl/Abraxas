from __future__ import annotations

import json

from abx.epistemics.epistemicScorecard import build_epistemic_quality_scorecard
from abx.epistemics.epistemicScorecardSerialization import serialize_epistemic_quality_scorecard


if __name__ == "__main__":
    scorecard = build_epistemic_quality_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_epistemic_quality_scorecard(scorecard))}, indent=2, sort_keys=True))
