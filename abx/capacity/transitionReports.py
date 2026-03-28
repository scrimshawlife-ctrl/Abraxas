from __future__ import annotations

from abx.capacity.capacityTransitions import build_budget_exhaustion_records, build_capacity_transition_records
from abx.capacity.types import CapacityGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_capacity_transition_report() -> dict[str, object]:
    transitions = build_capacity_transition_records()
    exhaustion = build_budget_exhaustion_records()
    errors = []
    for row in transitions:
        if row.to_state in {"BUDGET_EXHAUSTED", "ADMISSION_BLOCKED"}:
            errors.append(CapacityGovernanceErrorRecord("TRANSITION_BLOCKING", "ERROR", f"{row.resource_ref} state={row.to_state}"))
        elif row.to_state in {"GUARANTEE_DOWNGRADED", "RELEASE_REQUIRED"}:
            errors.append(CapacityGovernanceErrorRecord("TRANSITION_ATTENTION", "WARN", f"{row.resource_ref} state={row.to_state}"))
    report = {
        "artifactType": "CapacityTransitionAudit.v1",
        "artifactId": "capacity-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "exhaustion": [x.__dict__ for x in exhaustion],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
