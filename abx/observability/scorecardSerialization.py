from __future__ import annotations

from abx.observability.types import ObservabilityHealthScorecard
from abx.util.jsonutil import dumps_stable


def serialize_observability_scorecard(scorecard: ObservabilityHealthScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
