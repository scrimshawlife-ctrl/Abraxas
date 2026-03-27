from __future__ import annotations

from abx.agency.types import GuardrailPolicyRecord


def build_guardrail_inventory() -> list[GuardrailPolicyRecord]:
    rows = [
        GuardrailPolicyRecord(
            policy_id="guardrail.confirmation.required",
            applies_to=["OPERATOR_CONFIRMED_ACTION", "DELEGATED_ACTION", "BOUNDED_AUTONOMOUS_ACTION"],
            policy_class="CONFIRMATION_GATE",
            enforcement_state="PERMITTED_WITH_CONFIRMATION",
            ceiling="max_unconfirmed_actions=0",
        ),
        GuardrailPolicyRecord(
            policy_id="guardrail.delegation.depth",
            applies_to=["DELEGATED_ACTION", "BOUNDED_AUTONOMOUS_ACTION"],
            policy_class="DELEGATION_DEPTH",
            enforcement_state="PERMITTED_WITH_BUDGET",
            ceiling="max_depth=2",
        ),
        GuardrailPolicyRecord(
            policy_id="guardrail.retry.budget",
            applies_to=["DELEGATED_ACTION", "BOUNDED_AUTONOMOUS_ACTION"],
            policy_class="RETRY_BUDGET",
            enforcement_state="PERMITTED_WITH_BUDGET",
            ceiling="max_retry=2",
        ),
        GuardrailPolicyRecord(
            policy_id="guardrail.external.effects",
            applies_to=["BOUNDED_AUTONOMOUS_ACTION"],
            policy_class="EXTERNAL_SIDE_EFFECT",
            enforcement_state="HALTED",
            ceiling="external_writes=blocked_without_operator",
        ),
    ]
    return sorted(rows, key=lambda x: x.policy_id)
