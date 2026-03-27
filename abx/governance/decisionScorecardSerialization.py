from __future__ import annotations

from abx.governance.decision_types import DecisionGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_decision_scorecard(scorecard: DecisionGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
