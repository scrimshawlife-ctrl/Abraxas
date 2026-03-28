from __future__ import annotations

from abx.reconcile.conflictClassification import classify_conflict
from abx.reconcile.stateConflictRecords import build_state_conflict_records
from abx.reconcile.types import ReconciliationGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_state_conflict_report() -> dict[str, object]:
    conflicts = build_state_conflict_records()
    states = {x.conflict_id: classify_conflict(conflict_state=x.conflict_state, severity=x.severity) for x in conflicts}

    errors = []
    for row in conflicts:
        state = states[row.conflict_id]
        if state in {"BLOCKING_CONFLICT", "NOT_COMPUTABLE"}:
            errors.append(ReconciliationGovernanceErrorRecord("CONFLICT_BLOCKING", "ERROR", f"{row.conflict_id} state={state}"))
        elif state in {"CONFLICT_UNKNOWN", "COSMETIC_MISMATCH"}:
            errors.append(ReconciliationGovernanceErrorRecord("CONFLICT_ATTENTION", "WARN", f"{row.conflict_id} state={state}"))

    report = {
        "artifactType": "StateConflictAudit.v1",
        "artifactId": "state-conflict-audit",
        "conflicts": [x.__dict__ for x in conflicts],
        "conflictStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
