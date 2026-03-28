from __future__ import annotations

from abx.capacity.contentionBudgetRecords import (
    build_contention_budget_records,
    build_overcommitment_records,
    build_starvation_risk_records,
)
from abx.capacity.contentionClassification import classify_contention
from abx.capacity.types import CapacityGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_contention_budget_report() -> dict[str, object]:
    budget = build_contention_budget_records()
    overcommit = build_overcommitment_records()
    starvation = build_starvation_risk_records()
    states = {x.budget_id: classify_contention(contention_state=x.contention_state) for x in budget}
    errors = []
    for row in budget:
        state = states[row.budget_id]
        if state in {"CONTENTION_BLOCKING", "OVERCOMMITTED", "STARVATION_RISK", "NOT_COMPUTABLE"}:
            errors.append(CapacityGovernanceErrorRecord("CONTENTION_BLOCKING", "ERROR", f"{row.resource_ref} state={state}"))
        elif state in {"CONTENTION_ACTIVE"}:
            errors.append(CapacityGovernanceErrorRecord("CONTENTION_ATTENTION", "WARN", f"{row.resource_ref} state={state}"))
    report = {
        "artifactType": "ContentionBudgetAudit.v1",
        "artifactId": "contention-budget-audit",
        "budget": [x.__dict__ for x in budget],
        "overcommitment": [x.__dict__ for x in overcommit],
        "starvation": [x.__dict__ for x in starvation],
        "contentionStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
