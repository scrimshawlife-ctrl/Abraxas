from __future__ import annotations

from abx.approval.types import ExpiredApprovalRecord, RevokedApprovalRecord


def build_revoked_approval_records() -> tuple[RevokedApprovalRecord, ...]:
    return (
        RevokedApprovalRecord("rev.001", "apr.connector.001", "REVOKED", "withdrawn_after_incident"),
    )


def build_expired_approval_records() -> tuple[ExpiredApprovalRecord, ...]:
    return (
        ExpiredApprovalRecord("exp.001", "apr.override.001", "EXPIRED", "2026-03-18T09:00:00Z"),
    )
