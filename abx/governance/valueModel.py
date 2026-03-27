from __future__ import annotations

from abx.governance.decision_types import ValueModelRecord


def build_value_model() -> list[ValueModelRecord]:
    rows = [
        ValueModelRecord(
            value_id="value.determinism",
            value_term="determinism_priority",
            status="ENFORCED",
            linked_policies=["policy.boundary.validation", "policy.runtime.ordering"],
            linked_decisions=["decision.input.acceptance", "decision.scheduler.order"],
            owner="governance",
        ),
        ValueModelRecord(
            value_id="value.provenance",
            value_term="provenance_integrity",
            status="ENFORCED",
            linked_policies=["policy.boundary.trust", "policy.explain.provenance"],
            linked_decisions=["decision.trust.gate"],
            owner="governance",
        ),
        ValueModelRecord(
            value_id="value.containment",
            value_term="degradation_containment",
            status="MONITORED",
            linked_policies=["policy.resilience.degradation", "policy.override.precedence"],
            linked_decisions=["decision.degradation.route"],
            owner="operations",
        ),
    ]
    return sorted(rows, key=lambda x: x.value_id)
