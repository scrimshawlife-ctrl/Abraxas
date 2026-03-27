from __future__ import annotations

from abx.evidence.types import EvidenceTransitionRecord


def build_evidence_transition_records() -> tuple[EvidenceTransitionRecord, ...]:
    return (
        EvidenceTransitionRecord("etr.001", "RELEASE_DECISION", "BURDEN_UNMET", "BURDEN_PROVISIONALLY_MET", "added_replay_validation"),
        EvidenceTransitionRecord("etr.002", "POLICY_EXCEPTION", "BURDEN_PROVISIONALLY_MET", "BURDEN_UNMET", "contradictory_control_signal"),
        EvidenceTransitionRecord("etr.003", "PUBLICATION_DECISION", "BURDEN_MET", "CONFLICTING_EVIDENCE", "posthoc_source_divergence"),
        EvidenceTransitionRecord("etr.004", "ROLLBACK_DECISION", "BURDEN_PROVISIONALLY_MET", "BURDEN_MET", "incident_evidence_confirmed"),
        EvidenceTransitionRecord("etr.005", "LOW_RISK_TUNING", "BURDEN_MET", "READY_TO_DECIDE", "local_threshold_satisfied"),
    )
