from __future__ import annotations

from abx.tradeoff.types import TradeoffGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_tradeoff_scorecard(scorecard: TradeoffGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
