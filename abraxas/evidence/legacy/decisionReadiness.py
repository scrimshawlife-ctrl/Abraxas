from __future__ import annotations

from abx.evidence.types import DecisionReadinessRecord


def build_decision_readiness_inventory() -> tuple[DecisionReadinessRecord, ...]:
    return (
        DecisionReadinessRecord("ready.release", "RELEASE_DECISION", "READY_PROVISIONALLY", "burden_provisionally_met"),
        DecisionReadinessRecord("ready.override", "POLICY_EXCEPTION", "ESCALATED", "high_consequence_unmet"),
        DecisionReadinessRecord("ready.rollback", "ROLLBACK_DECISION", "READY_TO_DECIDE", "threshold_met"),
        DecisionReadinessRecord("ready.publish", "PUBLICATION_DECISION", "DEFERRED_PENDING_EVIDENCE", "conflicting_evidence"),
        DecisionReadinessRecord("ready.tuning", "LOW_RISK_TUNING", "READY_TO_DECIDE", "light_burden_met"),
    )
