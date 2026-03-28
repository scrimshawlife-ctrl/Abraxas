from __future__ import annotations

from abx.freshness.types import FreshnessGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_freshness_scorecard(scorecard: FreshnessGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
