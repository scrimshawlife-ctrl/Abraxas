from __future__ import annotations

from abx.evidence.types import EvidenceThresholdRecord


def build_threshold_inventory() -> tuple[EvidenceThresholdRecord, ...]:
    return (
        EvidenceThresholdRecord("thr.release.001", "RELEASE_DECISION", "HIGH", "LOW", "MIN_EVIDENCE_SCORE", 0.85),
        EvidenceThresholdRecord("thr.override.001", "POLICY_EXCEPTION", "HIGH", "LOW", "MIN_EVIDENCE_SCORE", 0.9),
        EvidenceThresholdRecord("thr.rollback.001", "ROLLBACK_DECISION", "MEDIUM", "HIGH", "MIN_EVIDENCE_SCORE", 0.6),
        EvidenceThresholdRecord("thr.publish.001", "PUBLICATION_DECISION", "MEDIUM", "MEDIUM", "MIN_EVIDENCE_SCORE", 0.75),
        EvidenceThresholdRecord("thr.tuning.001", "LOW_RISK_TUNING", "LOW", "HIGH", "MIN_EVIDENCE_SCORE", 0.45),
    )
