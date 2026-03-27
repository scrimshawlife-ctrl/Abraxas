from __future__ import annotations

import json

from abx.closure.closureScorecard import build_closure_ratification_scorecard
from abx.closure.closureScorecardSerialization import serialize_closure_ratification_scorecard


if __name__ == "__main__":
    scorecard = build_closure_ratification_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_closure_ratification_scorecard(scorecard))}, indent=2, sort_keys=True))
