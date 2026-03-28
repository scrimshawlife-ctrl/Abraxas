from __future__ import annotations

from abx.tradeoff.types import TradeoffGovernanceErrorRecord
from abx.tradeoff.valueWeightingRecords import build_value_weighting_records
from abx.tradeoff.weightingClassification import classify_weighting
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_value_weighting_report() -> dict[str, object]:
    rows = build_value_weighting_records()
    states = {x.weighting_id: classify_weighting(weighting_state=x.weighting_state, weighting_source=x.weighting_source) for x in rows}
    errors = []
    for row in rows:
        state = states[row.weighting_id]
        if state in {"HIDDEN_WEIGHTING_SUSPECTED", "VALUE_CONFLICT_UNRESOLVED"}:
            errors.append(TradeoffGovernanceErrorRecord("WEIGHTING_INTEGRITY_FAIL", "ERROR", f"{row.decision_ref} state={state}"))
        elif state in {"LOCAL_WEIGHTING_ACTIVE", "EMERGENCY_WEIGHTING_ACTIVE", "NOT_COMPUTABLE"}:
            errors.append(TradeoffGovernanceErrorRecord("WEIGHTING_ATTENTION_REQUIRED", "WARN", f"{row.decision_ref} state={state}"))

    report = {
        "artifactType": "ValueWeightingAudit.v1",
        "artifactId": "value-weighting-audit",
        "weighting": [x.__dict__ for x in rows],
        "weightingStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
