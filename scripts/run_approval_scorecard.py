from __future__ import annotations

import json

from abx.approval.approvalScorecard import build_approval_governance_scorecard
from abx.approval.approvalScorecardSerialization import serialize_approval_scorecard


if __name__ == "__main__":
    scorecard = build_approval_governance_scorecard()
    print(json.dumps({"scorecard": json.loads(serialize_approval_scorecard(scorecard))}, indent=2, sort_keys=True))
