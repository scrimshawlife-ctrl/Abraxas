from __future__ import annotations

from abx.reconcile.cosmeticAlignmentRecords import build_cosmetic_alignment_records
from abx.reconcile.lossyRepairRecords import build_lossy_repair_records
from abx.reconcile.reconciliationTransitions import build_reconciliation_transition_records
from abx.reconcile.types import ReconciliationGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_reconciliation_transition_report() -> dict[str, object]:
    transitions = build_reconciliation_transition_records()
    lossy = build_lossy_repair_records()
    cosmetic = build_cosmetic_alignment_records()

    errors = []
    for row in transitions:
        if row.to_state in {"UNRESOLVED_CONFLICT_ACTIVE", "NOT_COMPUTABLE"}:
            errors.append(ReconciliationGovernanceErrorRecord("TRANSITION_BLOCKING", "ERROR", f"{row.reconciliation_ref} state={row.to_state}"))
        elif row.to_state in {"COSMETIC_ALIGNMENT_ACTIVE", "VALIDATION_REQUIRED", "PROVISIONAL_RESTORED"}:
            errors.append(ReconciliationGovernanceErrorRecord("TRANSITION_ATTENTION", "WARN", f"{row.reconciliation_ref} state={row.to_state}"))

    report = {
        "artifactType": "ReconciliationTransitionAudit.v1",
        "artifactId": "reconciliation-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "lossyRepair": [x.__dict__ for x in lossy],
        "cosmeticAlignment": [x.__dict__ for x in cosmetic],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
