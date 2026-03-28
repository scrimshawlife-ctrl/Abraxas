from __future__ import annotations

from abx.operator.types import OperatorGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_operator_scorecard(scorecard: OperatorGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
