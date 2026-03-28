from __future__ import annotations

from abx.interface.crossBoundaryMismatchRecords import build_cross_boundary_mismatch_records
from abx.interface.degradedHandoffRecords import build_degraded_handoff_records
from abx.interface.handoffTransitions import build_delivery_transition_records
from abx.interface.types import InterfaceGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_interface_transition_report() -> dict[str, object]:
    transitions = build_delivery_transition_records()
    degraded = build_degraded_handoff_records()
    mismatch = build_cross_boundary_mismatch_records()
    errors = []
    for row in transitions:
        if row.to_state in {"HANDOFF_REJECTED", "NOT_COMPUTABLE"}:
            errors.append(InterfaceGovernanceErrorRecord("TRANSITION_BLOCKING", "ERROR", f"{row.handoff_ref} state={row.to_state}"))
        elif row.to_state in {"DELIVERY_PARTIAL", "DELIVERY_DUPLICATED"}:
            errors.append(InterfaceGovernanceErrorRecord("TRANSITION_ATTENTION", "WARN", f"{row.handoff_ref} state={row.to_state}"))
    report = {
        "artifactType": "InterfaceTransitionAudit.v1",
        "artifactId": "interface-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "degraded": [x.__dict__ for x in degraded],
        "mismatch": [x.__dict__ for x in mismatch],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
