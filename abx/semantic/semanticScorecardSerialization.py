from __future__ import annotations

from abx.semantic.types import SemanticGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_semantic_scorecard(scorecard: SemanticGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
