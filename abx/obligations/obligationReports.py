from __future__ import annotations

from abx.obligations.dischargeEvidence import build_discharge_evidence_records
from abx.obligations.obligationClassification import classify_obligation_lifecycle_state
from abx.obligations.obligationLifecycle import build_obligation_lifecycle_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_obligation_lifecycle_report() -> dict[str, object]:
    lifecycle = build_obligation_lifecycle_records()
    evidence = {x.commitment_id: x for x in build_discharge_evidence_records()}
    states = {
        row.commitment_id: classify_obligation_lifecycle_state(
            lifecycle_state=row.lifecycle_state,
            discharge_state=evidence[row.commitment_id].discharge_state,
        )
        for row in lifecycle
    }
    report = {
        "artifactType": "ObligationLifecycleAudit.v1",
        "artifactId": "obligation-lifecycle-audit",
        "lifecycle": [x.__dict__ for x in lifecycle],
        "dischargeEvidence": [x.__dict__ for x in evidence.values()],
        "obligationStates": states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
