from __future__ import annotations

from abx.docs_governance.types import DocumentationLegibilityScorecard
from abx.util.jsonutil import dumps_stable


def serialize_doc_legibility_scorecard(scorecard: DocumentationLegibilityScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
