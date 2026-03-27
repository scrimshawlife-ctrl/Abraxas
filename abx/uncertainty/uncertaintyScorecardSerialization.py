from __future__ import annotations

from abx.uncertainty.types import UncertaintyGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_uncertainty_scorecard(scorecard: UncertaintyGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
