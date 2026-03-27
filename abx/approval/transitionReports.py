from __future__ import annotations

from abx.approval.approvalTransitions import build_approval_transitions
from abx.approval.delegatedApprovals import build_delegated_approval_records
from abx.approval.revokedExpiredApprovals import build_expired_approval_records, build_revoked_approval_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_approval_transition_report() -> dict[str, object]:
    transitions = build_approval_transitions()
    delegated = build_delegated_approval_records()
    revoked = build_revoked_approval_records()
    expired = build_expired_approval_records()
    report = {
        "artifactType": "ApprovalTransitionAudit.v1",
        "artifactId": "approval-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "delegated": [x.__dict__ for x in delegated],
        "revoked": [x.__dict__ for x in revoked],
        "expired": [x.__dict__ for x in expired],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
