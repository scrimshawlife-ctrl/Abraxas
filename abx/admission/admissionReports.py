from __future__ import annotations

from abx.admission.admissionClassification import classify_admission
from abx.admission.changeAdmissionRecords import build_change_admission_records
from abx.admission.types import AdmissionGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_change_admission_report() -> dict[str, object]:
    rows = build_change_admission_records()
    states = {x.admission_id: classify_admission(admission_state=x.admission_state, evidence_state=x.evidence_state) for x in rows}

    errors = []
    for row in rows:
        state = states[row.admission_id]
        if state in {"ADMISSION_REJECTED", "ADMISSION_BLOCKED", "NOT_COMPUTABLE"}:
            errors.append(AdmissionGovernanceErrorRecord("ADMISSION_BLOCKING", "ERROR", f"{row.change_ref} state={state}"))
        elif state in {"ADMISSION_PENDING", "CHANGE_PROPOSED"}:
            errors.append(AdmissionGovernanceErrorRecord("ADMISSION_ATTENTION", "WARN", f"{row.change_ref} state={state}"))

    report = {
        "artifactType": "ChangeAdmissionAudit.v1",
        "artifactId": "change-admission-audit",
        "admissions": [x.__dict__ for x in rows],
        "admissionStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
