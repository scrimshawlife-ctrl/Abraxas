from __future__ import annotations

from abx.innovation.types import ExperimentationGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_experimentation_scorecard(scorecard: ExperimentationGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
