from __future__ import annotations

from abx.operator.manualDriftRecords import build_manual_drift_records
from abx.operator.operatorTransitions import build_operator_transition_records
from abx.operator.restorationRecords import build_restoration_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_operator_transition_report() -> dict[str, object]:
    transitions = build_operator_transition_records()
    drift = build_manual_drift_records()
    restorations = build_restoration_records()

    transition_states = {x.transition_id: x.to_state for x in transitions}
    report = {
        "artifactType": "OperatorTransitionAudit.v1",
        "artifactId": "operator-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "transitionStates": transition_states,
        "manualDrift": [x.__dict__ for x in drift],
        "restorations": [x.__dict__ for x in restorations],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
