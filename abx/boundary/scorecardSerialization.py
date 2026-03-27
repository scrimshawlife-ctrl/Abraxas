from __future__ import annotations

from abx.boundary.types import BoundaryHealthScorecard
from abx.util.jsonutil import dumps_stable


def serialize_scorecard(scorecard: BoundaryHealthScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
