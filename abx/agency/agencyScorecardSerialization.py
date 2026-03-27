from __future__ import annotations

from abx.agency.types import AutonomousOperationScorecard
from abx.util.jsonutil import dumps_stable


def serialize_agency_scorecard(scorecard: AutonomousOperationScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
