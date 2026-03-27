from __future__ import annotations

from abx.knowledge.types import KnowledgeContinuityScorecard
from abx.util.jsonutil import dumps_stable


def serialize_knowledge_scorecard(scorecard: KnowledgeContinuityScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
