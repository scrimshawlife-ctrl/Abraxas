from __future__ import annotations

import json

from abx.meta.metaScorecard import build_meta_governance_scorecard
from abx.meta.metaScorecardSerialization import serialize_meta_governance_scorecard


if __name__ == "__main__":
    scorecard = build_meta_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_meta_governance_scorecard(scorecard))}, indent=2, sort_keys=True))
