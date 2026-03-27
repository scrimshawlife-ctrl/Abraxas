from __future__ import annotations

from abx.obligations.types import ObligationGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_obligation_scorecard(scorecard: ObligationGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
