from __future__ import annotations

from abx.tradeoff.priorityOverrideRecords import build_priority_override_records
from abx.tradeoff.types import TradeoffGovernanceErrorRecord
from abx.tradeoff.valueDriftRecords import build_value_drift_records
from abx.tradeoff.weightingTransitions import build_weighting_transition_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_weighting_transition_report() -> dict[str, object]:
    transitions = build_weighting_transition_records()
    drift = build_value_drift_records()
    overrides = build_priority_override_records()

    errors = []
    for row in transitions:
        if row.to_state in {"HIDDEN_WEIGHTING_ACTIVE", "STICKY_OVERRIDE_DETECTED"}:
            errors.append(TradeoffGovernanceErrorRecord("WEIGHTING_TRANSITION_FAIL", "ERROR", f"{row.decision_ref} to={row.to_state}"))
        elif row.to_state in {"LOCAL_OPTIMIZATION_ACTIVE", "VALUE_DRIFT_DETECTED"}:
            errors.append(TradeoffGovernanceErrorRecord("WEIGHTING_REBALANCE_REQUIRED", "WARN", f"{row.decision_ref} to={row.to_state}"))

    report = {
        "artifactType": "WeightingTransitionAudit.v1",
        "artifactId": "weighting-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "valueDrift": [x.__dict__ for x in drift],
        "overrides": [x.__dict__ for x in overrides],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
