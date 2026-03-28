from __future__ import annotations

from abx.identity.types import IdentityGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_identity_scorecard(scorecard: IdentityGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
