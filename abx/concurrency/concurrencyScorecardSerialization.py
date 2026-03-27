from __future__ import annotations

from abx.concurrency.types import ConcurrentOperationScorecard
from abx.util.jsonutil import dumps_stable


def serialize_concurrency_scorecard(scorecard: ConcurrentOperationScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
