from __future__ import annotations

from abx.reconcile.restorationInventory import build_restoration_inventory
from abx.reconcile.types import RestorationStatusRecord


def build_restoration_status_records() -> list[RestorationStatusRecord]:
    return [
        RestorationStatusRecord(
            restoration_id=restoration_id,
            reconciliation_ref=reconciliation_ref,
            restoration_state=restoration_state,
            validation_state=validation_state,
        )
        for restoration_id, reconciliation_ref, restoration_state, validation_state in build_restoration_inventory()
    ]
