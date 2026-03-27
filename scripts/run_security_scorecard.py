from __future__ import annotations

import json

from abx.security.securityScorecard import build_security_integrity_scorecard
from abx.security.securityScorecardSerialization import serialize_security_integrity_scorecard


if __name__ == "__main__":
    scorecard = build_security_integrity_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_security_integrity_scorecard(scorecard))}, indent=2, sort_keys=True))
