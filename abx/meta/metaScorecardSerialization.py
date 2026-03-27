from __future__ import annotations

from abx.meta.types import MetaGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_meta_governance_scorecard(scorecard: MetaGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
