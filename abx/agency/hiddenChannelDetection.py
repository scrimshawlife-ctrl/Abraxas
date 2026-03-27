from __future__ import annotations

from abx.agency.actionBoundaryInventory import build_action_boundary_inventory
from abx.agency.types import HiddenChannelRecord


def build_hidden_channel_records() -> list[HiddenChannelRecord]:
    rows: list[HiddenChannelRecord] = []
    for row in build_action_boundary_inventory():
        if row.governance_state == "HIDDEN_CHANNEL_SUSPECTED":
            risk = "HIDDEN_CHANNEL_SUSPECTED"
            status = "OPEN"
            reason = "direct_script_entry_can_trigger_action_without_unified_agency_gate"
        elif row.governance_state == "SIDE_EFFECT_BLOCKED":
            risk = "SIDE_EFFECT_BLOCKED"
            status = "CONTAINED"
            reason = "channel_exists_but_guardrail_blocks_external_effect"
        else:
            risk = "NO_HIDDEN_CHANNEL"
            status = "CLEAR"
            reason = "transition_is_explicitly_classified"
        rows.append(
            HiddenChannelRecord(
                channel_id=f"hidden.{row.boundary_id}",
                surface_id=row.surface_id,
                risk_class=risk,
                status=status,
                reason=reason,
            )
        )
    return sorted(rows, key=lambda x: x.channel_id)
