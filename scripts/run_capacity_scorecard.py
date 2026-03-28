from __future__ import annotations

import json

from abx.capacity.capacityScorecard import build_capacity_governance_scorecard
from abx.capacity.capacityScorecardSerialization import serialize_capacity_scorecard


if __name__ == "__main__":
    scorecard = build_capacity_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_capacity_scorecard(scorecard))}, indent=2, sort_keys=True))
