from __future__ import annotations

from abx.governance.decision_types import PolicySurfaceRecord


def build_policy_inventory() -> list[PolicySurfaceRecord]:
    rows = [
        PolicySurfaceRecord(
            policy_id="policy.boundary.validation",
            surface="abx.boundary.validation.validate_envelope",
            classification="authoritative",
            owner="governance",
            consumed_by=["decision.input.acceptance"],
        ),
        PolicySurfaceRecord(
            policy_id="policy.boundary.trust",
            surface="abx.boundary.trustEnforcement.enforce_trust_for_authoritative_mutation",
            classification="authoritative",
            owner="governance",
            consumed_by=["decision.trust.gate"],
        ),
        PolicySurfaceRecord(
            policy_id="policy.runtime.ordering",
            surface="abx.ers_scheduler.order_tasks",
            classification="derived",
            owner="runtime",
            consumed_by=["decision.scheduler.order"],
        ),
        PolicySurfaceRecord(
            policy_id="policy.override.precedence",
            surface="abx.governance.overridePrecedence.build_override_precedence",
            classification="authoritative",
            owner="governance",
            consumed_by=["decision.override.resolve"],
        ),
    ]
    return sorted(rows, key=lambda x: x.policy_id)
