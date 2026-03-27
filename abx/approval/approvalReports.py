from __future__ import annotations

from abx.approval.approvalClassification import classify_approval_state
from abx.approval.humanApprovalRecords import build_human_approval_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_human_approval_report() -> dict[str, object]:
    records = build_human_approval_records()
    states = {
        row.approval_id: classify_approval_state(
            approval_required=row.approval_required,
            approver_id=row.approver_id,
            raw_signal=row.raw_signal,
            valid_until=row.valid_until,
        )
        for row in records
    }
    report = {
        "artifactType": "HumanApprovalAudit.v1",
        "artifactId": "human-approval-audit",
        "approvals": [x.__dict__ for x in records],
        "approvalStates": states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
