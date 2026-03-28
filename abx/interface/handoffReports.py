from __future__ import annotations

from abx.interface.deliveryClassification import classify_handoff
from abx.interface.handoffStateRecords import build_delivery_records, build_handoff_state_records
from abx.interface.types import InterfaceGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_handoff_reliability_report() -> dict[str, object]:
    handoff = build_handoff_state_records()
    delivery = build_delivery_records()
    states = {x.handoff_id: classify_handoff(handoff_state=x.handoff_state) for x in handoff}
    errors = []
    for row in handoff:
        state = states[row.handoff_id]
        if state in {"HANDOFF_FAILED", "NOT_COMPUTABLE"}:
            errors.append(InterfaceGovernanceErrorRecord("HANDOFF_BLOCKING", "ERROR", f"{row.boundary_ref} state={state}"))
        elif state in {"HANDOFF_PENDING", "HANDOFF_UNKNOWN", "HANDOFF_SENT"}:
            errors.append(InterfaceGovernanceErrorRecord("HANDOFF_ATTENTION", "WARN", f"{row.boundary_ref} state={state}"))
    report = {
        "artifactType": "HandoffReliabilityAudit.v1",
        "artifactId": "handoff-reliability-audit",
        "handoff": [x.__dict__ for x in handoff],
        "delivery": [x.__dict__ for x in delivery],
        "handoffStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
