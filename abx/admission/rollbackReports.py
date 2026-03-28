from __future__ import annotations

from abx.admission.rejectionRecords import build_rejection_records
from abx.admission.rollbackRecords import build_rollback_records
from abx.admission.types import AdmissionGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_rejection_rollback_report() -> dict[str, object]:
    rejection = build_rejection_records()
    rollback = build_rollback_records()

    errors = []
    for row in rejection:
        if row.rejection_state in {"REJECTED", "RE_ADMISSION_REQUIRED"}:
            errors.append(AdmissionGovernanceErrorRecord("ADMISSION_REJECTION", "ERROR", f"{row.change_ref} state={row.rejection_state}"))
        elif row.rejection_state in {"DEFERRED"}:
            errors.append(AdmissionGovernanceErrorRecord("ADMISSION_DEFERRAL", "WARN", f"{row.change_ref} state={row.rejection_state}"))

    for row in rollback:
        if row.rollback_state in {"ROLLBACK_TRIGGERED", "RE_ADMISSION_REQUIRED"}:
            errors.append(AdmissionGovernanceErrorRecord("ROLLBACK_ACTIVE", "ERROR", f"{row.change_ref} state={row.rollback_state}"))

    report = {
        "artifactType": "RejectionRollbackAudit.v1",
        "artifactId": "rejection-rollback-audit",
        "rejection": [x.__dict__ for x in rejection],
        "rollback": [x.__dict__ for x in rollback],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
