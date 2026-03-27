from __future__ import annotations

from abx.performance.types import PerformanceResourceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_performance_resource_scorecard(scorecard: PerformanceResourceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
