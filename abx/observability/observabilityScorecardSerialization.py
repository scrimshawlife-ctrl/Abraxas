from __future__ import annotations

from abx.observability.types import ObservabilityGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_observability_scorecard(scorecard: ObservabilityGovernanceScorecard) -> str:
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
