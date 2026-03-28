from __future__ import annotations

from abx.explanation.types import ExplanationGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_explanation_scorecard(scorecard: ExplanationGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
