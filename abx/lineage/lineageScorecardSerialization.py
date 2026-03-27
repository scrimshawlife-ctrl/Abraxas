from __future__ import annotations

from abx.lineage.types import LineageGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_lineage_scorecard(scorecard: LineageGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
