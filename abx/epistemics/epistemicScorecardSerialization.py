from __future__ import annotations

from abx.epistemics.types import EpistemicQualityScorecard
from abx.util.jsonutil import dumps_stable


def serialize_epistemic_quality_scorecard(scorecard: EpistemicQualityScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
