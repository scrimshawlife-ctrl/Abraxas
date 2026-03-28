from __future__ import annotations

import json

from abx.identity.identityScorecard import build_identity_governance_scorecard
from abx.identity.identityScorecardSerialization import serialize_identity_scorecard


if __name__ == "__main__":
    scorecard = build_identity_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_identity_scorecard(scorecard))}, indent=2, sort_keys=True))
