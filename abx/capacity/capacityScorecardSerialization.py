from __future__ import annotations

from abx.capacity.types import CapacityGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_capacity_scorecard(scorecard: CapacityGovernanceScorecard) -> str:
    return dumps_stable(
        {
            "artifactType": scorecard.artifact_type,
            "artifactId": scorecard.artifact_id,
            "dimensions": scorecard.dimensions,
            "evidence": scorecard.evidence,
            "blockers": scorecard.blockers,
            "category": scorecard.category,
            "scorecardHash": scorecard.scorecard_hash,
        }
    )
