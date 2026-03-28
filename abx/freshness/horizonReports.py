from __future__ import annotations

from abx.freshness.horizonClassification import classify_horizon
from abx.freshness.timeHorizonRecords import build_time_horizon_records
from abx.freshness.types import FreshnessGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_time_horizon_report() -> dict[str, object]:
    rows = build_time_horizon_records()
    states = {x.horizon_id: classify_horizon(horizon_state=x.horizon_state, cadence_ref=x.cadence_ref) for x in rows}
    errors = []
    for row in rows:
        state = states[row.horizon_id]
        if state == "BLOCKED":
            errors.append(FreshnessGovernanceErrorRecord("HORIZON_BLOCKED", "ERROR", f"{row.entity_ref} state={state}"))
        elif state in {"HORIZON_UNKNOWN", "NOT_COMPUTABLE"}:
            errors.append(FreshnessGovernanceErrorRecord("HORIZON_ATTENTION_REQUIRED", "WARN", f"{row.entity_ref} state={state}"))

    report = {
        "artifactType": "TimeHorizonAudit.v1",
        "artifactId": "time-horizon-audit",
        "horizons": [x.__dict__ for x in rows],
        "horizonStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
