from __future__ import annotations

from abx.admission.rollbackInventory import build_rejection_inventory
from abx.admission.types import RejectionRecord


def build_rejection_records() -> list[RejectionRecord]:
    return [
        RejectionRecord(rejection_id=rid, change_ref=cref, rejection_state=state, rejection_reason=reason)
        for rid, cref, state, reason in build_rejection_inventory()
    ]
