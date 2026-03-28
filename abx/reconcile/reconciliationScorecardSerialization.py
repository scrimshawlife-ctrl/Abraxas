from __future__ import annotations

from abx.reconcile.types import ReconciliationGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_reconciliation_scorecard(scorecard: ReconciliationGovernanceScorecard) -> str:
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
