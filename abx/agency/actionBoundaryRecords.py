from __future__ import annotations

from abx.agency.actionBoundaryInventory import build_action_boundary_inventory
from abx.agency.types import SideEffectRecord


def build_side_effect_records() -> list[SideEffectRecord]:
    rows = [
        SideEffectRecord(
            effect_id=f"effect.{row.boundary_id}",
            surface_id=row.surface_id,
            effect_class=row.governance_state,
            evidence_ref=row.boundary_id,
        )
        for row in build_action_boundary_inventory()
        if row.side_effect_capability == "SIDE_EFFECT_CAPABLE"
    ]
    return sorted(rows, key=lambda x: x.effect_id)
