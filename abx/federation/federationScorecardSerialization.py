from __future__ import annotations

from abx.federation.types import FederationGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_federation_scorecard(scorecard: FederationGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
