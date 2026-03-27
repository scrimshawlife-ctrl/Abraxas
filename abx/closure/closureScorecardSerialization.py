from __future__ import annotations

from abx.closure.types import ClosureRatificationScorecard
from abx.util.jsonutil import dumps_stable


def serialize_closure_ratification_scorecard(scorecard: ClosureRatificationScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
