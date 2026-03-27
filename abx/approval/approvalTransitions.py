from __future__ import annotations

from abx.approval.types import ApprovalTransitionRecord


def build_approval_transitions() -> tuple[ApprovalTransitionRecord, ...]:
    return (
        ApprovalTransitionRecord("trn.001", "apr.deploy.001", "APPROVAL_REQUESTED", "APPROVAL_GRANTED", "explicit_signoff"),
        ApprovalTransitionRecord("trn.002", "apr.override.001", "APPROVAL_GRANTED", "APPROVAL_EXPIRED", "time_window_elapsed"),
        ApprovalTransitionRecord("trn.003", "apr.destroy.001", "APPROVAL_REQUESTED", "APPROVAL_DENIED", "risk_unacceptable"),
        ApprovalTransitionRecord("trn.004", "apr.connector.001", "APPROVAL_GRANTED", "APPROVAL_WITHDRAWN", "post_incident_reassessment"),
        ApprovalTransitionRecord("trn.005", "apr.external.001", "APPROVAL_REQUESTED", "APPROVAL_CONDITIONAL", "requires_rollback_plan"),
        ApprovalTransitionRecord("trn.006", "apr.external.001", "APPROVAL_CONDITIONAL", "APPROVAL_GRANTED", "conditions_satisfied"),
        ApprovalTransitionRecord("trn.007", "apr.external.001", "APPROVAL_GRANTED", "DELEGATED", "bounded_delegation"),
        ApprovalTransitionRecord("trn.008", "apr.publish.001", "APPROVAL_REQUIRED", "BLOCKED_PENDING_APPROVAL", "no_explicit_consent"),
    )
