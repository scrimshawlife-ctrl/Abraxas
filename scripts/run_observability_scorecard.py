from __future__ import annotations

import json

from abx.observability.observabilityScorecard import build_observability_governance_scorecard
from abx.observability.observabilityScorecardSerialization import serialize_observability_scorecard


if __name__ == "__main__":
    scorecard = build_observability_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_observability_scorecard(scorecard))}, indent=2, sort_keys=True))
