from __future__ import annotations

from abx.failure.types import FailureGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_failure_scorecard(scorecard: FailureGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
