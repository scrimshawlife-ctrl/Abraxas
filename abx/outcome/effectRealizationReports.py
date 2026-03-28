from __future__ import annotations

from abx.outcome.effectRealizationClassification import classify_effect_realization
from abx.outcome.effectRealizationRecords import build_effect_realization_records, build_outcome_verification_records
from abx.outcome.types import OutcomeGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_effect_realization_report() -> dict[str, object]:
    realization = build_effect_realization_records()
    verification = build_outcome_verification_records()
    states = {
        x.realization_id: classify_effect_realization(realization_state=x.realization_state, evidence_mode=x.evidence_mode)
        for x in realization
    }
    errors = []
    for row in realization:
        state = states[row.realization_id]
        if state in {"NOT_COMPUTABLE", "VERIFICATION_REQUIRED"}:
            errors.append(OutcomeGovernanceErrorRecord("EFFECT_VERIFICATION_BLOCKING", "ERROR", f"{row.action_ref} state={state}"))
        elif state in {"EFFECT_INFERRED", "EFFECT_ACKNOWLEDGED"}:
            errors.append(OutcomeGovernanceErrorRecord("EFFECT_VERIFICATION_ATTENTION", "WARN", f"{row.action_ref} state={state}"))
    report = {
        "artifactType": "EffectRealizationAudit.v1",
        "artifactId": "effect-realization-audit",
        "realization": [x.__dict__ for x in realization],
        "verification": [x.__dict__ for x in verification],
        "realizationStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
