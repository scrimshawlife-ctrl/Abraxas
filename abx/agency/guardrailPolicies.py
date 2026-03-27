from __future__ import annotations

from abx.agency.guardrailInventory import build_guardrail_inventory
from abx.agency.types import GuardrailTriggerRecord


def build_guardrail_triggers() -> list[GuardrailTriggerRecord]:
    triggers: list[GuardrailTriggerRecord] = []
    for row in build_guardrail_inventory():
        if row.enforcement_state == "HALTED":
            state = "TRIPPED"
            reason = "external_side_effect_without_operator_gate"
        else:
            state = "NO_TRIP"
            reason = "within_guardrail_ceiling"
        triggers.append(
            GuardrailTriggerRecord(
                trigger_id=f"trigger.{row.policy_id}",
                policy_id=row.policy_id,
                trigger_state=state,
                reason=reason,
            )
        )
    return sorted(triggers, key=lambda x: x.trigger_id)
