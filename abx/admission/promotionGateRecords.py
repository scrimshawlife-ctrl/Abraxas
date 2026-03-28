from __future__ import annotations

from abx.admission.promotionInventory import build_promotion_inventory
from abx.admission.types import PromotionGateRecord


def build_promotion_gate_records() -> list[PromotionGateRecord]:
    return [
        PromotionGateRecord(gate_id=gid, change_ref=cref, promotion_state=state, gate_reason=reason)
        for gid, cref, state, reason in build_promotion_inventory()
    ]
