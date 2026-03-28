from __future__ import annotations

from abx.reconcile.conflictInventory import build_conflict_inventory
from abx.reconcile.types import StateConflictRecord


def build_state_conflict_records() -> list[StateConflictRecord]:
    return [
        StateConflictRecord(
            conflict_id=conflict_id,
            left_surface=left_surface,
            right_surface=right_surface,
            conflict_state=conflict_state,
            severity=severity,
        )
        for conflict_id, left_surface, right_surface, conflict_state, severity in build_conflict_inventory()
    ]
