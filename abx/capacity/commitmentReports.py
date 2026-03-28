from __future__ import annotations

from abx.capacity.allocationClassification import classify_commitment
from abx.capacity.capacityCommitmentRecords import build_allocation_records, build_capacity_commitment_records
from abx.capacity.types import CapacityGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_capacity_commitment_report() -> dict[str, object]:
    commitment = build_capacity_commitment_records()
    allocation = build_allocation_records()
    a_idx = {x.resource_ref: x for x in allocation}
    states = {
        x.commitment_id: classify_commitment(commitment_state=x.commitment_state, allocation_state=a_idx[x.resource_ref].allocation_state)
        for x in commitment
    }
    errors = []
    for row in commitment:
        state = states[row.commitment_id]
        if state in {"BLOCKED", "NOT_COMPUTABLE"}:
            errors.append(CapacityGovernanceErrorRecord("COMMITMENT_BLOCKING", "ERROR", f"{row.resource_ref} state={state}"))
        elif state in {"COMMITMENT_UNKNOWN", "BEST_EFFORT_CLAIM", "SOFT_CAPACITY_COMMITTED"}:
            errors.append(CapacityGovernanceErrorRecord("COMMITMENT_ATTENTION", "WARN", f"{row.resource_ref} state={state}"))
    report = {
        "artifactType": "CapacityCommitmentAudit.v1",
        "artifactId": "capacity-commitment-audit",
        "commitment": [x.__dict__ for x in commitment],
        "allocation": [x.__dict__ for x in allocation],
        "commitmentStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
