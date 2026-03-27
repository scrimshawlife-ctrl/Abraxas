from __future__ import annotations

from abx.human_factors.types import UXHumanFactorsScorecard
from abx.util.jsonutil import dumps_stable


def serialize_human_factors_scorecard(scorecard: UXHumanFactorsScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
