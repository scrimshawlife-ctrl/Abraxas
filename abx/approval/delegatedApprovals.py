from __future__ import annotations

from abx.approval.types import DelegatedApprovalRecord


def build_delegated_approval_records() -> tuple[DelegatedApprovalRecord, ...]:
    return (
        DelegatedApprovalRecord(
            delegation_id="del.001",
            approval_id="apr.external.001",
            delegated_by="steward.commercial",
            delegated_to="delegate.commercial",
            delegated_scope="commitment/ext/partner-a",
            delegation_valid_until="2026-03-29T00:00:00Z",
            delegation_state="AUTHORITY_DELEGATED",
        ),
        DelegatedApprovalRecord(
            delegation_id="del.002",
            approval_id="apr.publish.001",
            delegated_by="observer.comms",
            delegated_to="intern.comms",
            delegated_scope="public/forecast/v22",
            delegation_valid_until="2026-04-01T00:00:00Z",
            delegation_state="DELEGATION_INVALID",
        ),
    )
