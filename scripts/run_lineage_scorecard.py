from __future__ import annotations

import json

from abx.lineage.lineageScorecard import build_lineage_governance_scorecard
from abx.lineage.lineageScorecardSerialization import serialize_lineage_scorecard


if __name__ == "__main__":
    scorecard = build_lineage_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_lineage_scorecard(scorecard))}, indent=2, sort_keys=True))
