from __future__ import annotations

from abx.obligations.commitmentInventory import build_commitment_inventory
from abx.obligations.deadlineRecords import build_deadline_records
from abx.obligations.dueStateClassification import classify_due_state
from abx.obligations.types import DueStateRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_due_state_report() -> dict[str, object]:
    commitments = {x.commitment_id: x for x in build_commitment_inventory()}
    deadlines = build_deadline_records()
    due_states = [
        DueStateRecord(
            due_state_id=f"due.{row.deadline_id}",
            deadline_id=row.deadline_id,
            due_state=classify_due_state(
                deadline_kind=row.deadline_kind,
                commitment_state=commitments[row.commitment_id].commitment_state,
                due_date=row.due_date,
            )[0],
            risk_state=classify_due_state(
                deadline_kind=row.deadline_kind,
                commitment_state=commitments[row.commitment_id].commitment_state,
                due_date=row.due_date,
            )[1],
        )
        for row in deadlines
    ]
    report = {
        "artifactType": "DueStateAudit.v1",
        "artifactId": "due-state-audit",
        "deadlines": [x.__dict__ for x in deadlines],
        "dueStates": [x.__dict__ for x in due_states],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
