from __future__ import annotations

from abx.admission.rollbackInventory import build_rollback_inventory
from abx.admission.types import RollbackRecord


def build_rollback_records() -> list[RollbackRecord]:
    return [
        RollbackRecord(rollback_id=rid, change_ref=cref, rollback_state=state, rollback_reason=reason)
        for rid, cref, state, reason in build_rollback_inventory()
    ]
