from __future__ import annotations

from abx.continuity.types import MissionContinuityScorecard
from abx.util.jsonutil import dumps_stable


def serialize_continuity_scorecard(scorecard: MissionContinuityScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
