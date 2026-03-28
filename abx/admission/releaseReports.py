from __future__ import annotations

from abx.admission.readinessClassification import classify_release_readiness
from abx.admission.releaseReadinessRecords import build_release_readiness_records
from abx.admission.types import AdmissionGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_release_readiness_report() -> dict[str, object]:
    rows = build_release_readiness_records()
    states = {x.readiness_id: classify_release_readiness(readiness_state=x.readiness_state) for x in rows}

    errors = []
    for row in rows:
        state = states[row.readiness_id]
        if state in {"RELEASE_BLOCKED", "ROLLBACK_REQUIRED", "NOT_COMPUTABLE"}:
            errors.append(AdmissionGovernanceErrorRecord("RELEASE_BLOCKING", "ERROR", f"{row.change_ref} state={state}"))
        elif state in {"RELEASE_PROVISIONAL", "EXPERIMENTAL"}:
            errors.append(AdmissionGovernanceErrorRecord("RELEASE_ATTENTION", "WARN", f"{row.change_ref} state={state}"))

    report = {
        "artifactType": "ReleaseReadinessAudit.v1",
        "artifactId": "release-readiness-audit",
        "readiness": [x.__dict__ for x in rows],
        "readinessStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
