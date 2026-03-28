from __future__ import annotations

from abx.tradeoff.priorityAssignmentRecords import build_priority_assignment_records
from abx.tradeoff.priorityClassification import classify_priority
from abx.tradeoff.types import TradeoffGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_priority_assignment_report() -> dict[str, object]:
    rows = build_priority_assignment_records()
    states = {x.priority_id: classify_priority(priority_state=x.priority_state, tie_breaker=x.tie_breaker) for x in rows}
    errors = []
    for row in rows:
        state = states[row.priority_id]
        if state in {"PRIORITY_CONFLICT", "BLOCKED"}:
            errors.append(TradeoffGovernanceErrorRecord("PRIORITY_ASSIGNMENT_FAIL", "ERROR", f"{row.decision_ref} state={state}"))
        elif state in {"EMERGENCY_PRIORITY_OVERRIDE", "TEMPORARY_PRIORITY_OVERRIDE", "PRIORITY_UNKNOWN"}:
            errors.append(TradeoffGovernanceErrorRecord("PRIORITY_ATTENTION_REQUIRED", "WARN", f"{row.decision_ref} state={state}"))

    report = {
        "artifactType": "PriorityAssignmentAudit.v1",
        "artifactId": "priority-assignment-audit",
        "priority": [x.__dict__ for x in rows],
        "priorityStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
