from __future__ import annotations

from abx.admission.promotionClassification import classify_promotion
from abx.admission.promotionGateRecords import build_promotion_gate_records
from abx.admission.types import AdmissionGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_promotion_gate_report() -> dict[str, object]:
    rows = build_promotion_gate_records()
    states = {x.gate_id: classify_promotion(promotion_state=x.promotion_state) for x in rows}

    errors = []
    for row in rows:
        state = states[row.gate_id]
        if state in {"PROMOTION_FAILED_GATE", "NOT_COMPUTABLE"}:
            errors.append(AdmissionGovernanceErrorRecord("PROMOTION_BLOCKING", "ERROR", f"{row.change_ref} state={state}"))
        elif state in {"PROMOTION_GATED", "PROMOTION_DEFERRED", "PROMOTION_CANDIDATE"}:
            errors.append(AdmissionGovernanceErrorRecord("PROMOTION_ATTENTION", "WARN", f"{row.change_ref} state={state}"))

    report = {
        "artifactType": "PromotionGateAudit.v1",
        "artifactId": "promotion-gate-audit",
        "promotion": [x.__dict__ for x in rows],
        "promotionStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
