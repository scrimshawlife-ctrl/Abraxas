from __future__ import annotations

from abx.evidence.types import EvidenceGovernanceScorecard
from abx.util.jsonutil import dumps_stable


def serialize_evidence_scorecard(scorecard: EvidenceGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
