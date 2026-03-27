from __future__ import annotations

from abx.approval.types import ApprovalGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_approval_scorecard(scorecard: ApprovalGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
