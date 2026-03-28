from __future__ import annotations

from abx.explanation.honestyClassification import classify_honesty
from abx.explanation.interpretiveHonestyRecords import (
    build_causal_language_records,
    build_interpretive_honesty_records,
    build_omission_risk_records,
)
from abx.explanation.types import ExplanationGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_interpretive_honesty_report() -> dict[str, object]:
    honesty = build_interpretive_honesty_records()
    causal = build_causal_language_records()
    omission = build_omission_risk_records()
    causal_by_surface = {x.surface_ref: x for x in causal}
    omission_by_surface = {x.surface_ref: x for x in omission}
    honesty_states = {}
    for row in honesty:
        causal_row = causal_by_surface.get(row.surface_ref)
        omission_row = omission_by_surface.get(row.surface_ref)
        honesty_states[row.honesty_id] = classify_honesty(
            honesty_state=row.honesty_state,
            causal_state=causal_row.causal_state if causal_row else "CAUSAL_LANGUAGE_ABSTAINED",
            support_state=causal_row.support_state if causal_row else "SUFFICIENT",
            omission_state=omission_row.omission_state if omission_row else "OMISSION_CLEAR",
        )

    errors = []
    for row in honesty:
        state = honesty_states[row.honesty_id]
        if state in {"UNSUPPORTED_EXPLANATORY_JUMP", "CAUSAL_OVERREACH_RISK"}:
            errors.append(ExplanationGovernanceErrorRecord("INTERPRETIVE_OVERREACH", "ERROR", f"{row.surface_ref} state={state}"))
        elif state in {"CAVEAT_OMISSION_RISK", "NOT_COMPUTABLE"}:
            errors.append(ExplanationGovernanceErrorRecord("INTERPRETIVE_ATTENTION_REQUIRED", "WARN", f"{row.surface_ref} state={state}"))

    report = {
        "artifactType": "InterpretiveHonestyAudit.v1",
        "artifactId": "interpretive-honesty-audit",
        "honesty": [x.__dict__ for x in honesty],
        "causal": [x.__dict__ for x in causal],
        "omission": [x.__dict__ for x in omission],
        "honestyStates": honesty_states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
