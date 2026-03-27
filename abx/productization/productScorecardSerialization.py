from __future__ import annotations

from abx.productization.types import ProductizationGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_productization_scorecard(scorecard: ProductizationGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
