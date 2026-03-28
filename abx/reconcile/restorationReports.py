from __future__ import annotations

from abx.reconcile.restorationClassification import classify_restoration
from abx.reconcile.restorationStatusRecords import build_restoration_status_records
from abx.reconcile.types import ReconciliationGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_restoration_status_report() -> dict[str, object]:
    restoration = build_restoration_status_records()
    states = {x.restoration_id: classify_restoration(restoration_state=x.restoration_state, validation_state=x.validation_state) for x in restoration}

    errors = []
    for row in restoration:
        state = states[row.restoration_id]
        if state in {"BLOCKED", "NOT_COMPUTABLE"}:
            errors.append(ReconciliationGovernanceErrorRecord("RESTORATION_BLOCKED", "ERROR", f"{row.reconciliation_ref} state={state}"))
        elif state in {"COSMETIC_ALIGNMENT_ONLY", "PROVISIONAL_OR_PENDING", "CONSISTENCY_PARTIALLY_RESTORED"}:
            errors.append(ReconciliationGovernanceErrorRecord("RESTORATION_ATTENTION", "WARN", f"{row.reconciliation_ref} state={state}"))

    report = {
        "artifactType": "RestorationStatusAudit.v1",
        "artifactId": "restoration-status-audit",
        "restoration": [x.__dict__ for x in restoration],
        "restorationStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
