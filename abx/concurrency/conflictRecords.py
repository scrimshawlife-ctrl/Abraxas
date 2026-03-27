from __future__ import annotations

from abx.concurrency.conflictClassification import classify_conflict_resolution_hint
from abx.concurrency.conflictInventory import build_conflict_inventory
from abx.concurrency.types import ConflictClassificationRecord


def build_conflict_classification_records() -> list[ConflictClassificationRecord]:
    rows = [
        ConflictClassificationRecord(
            classification_id=f"classification.{row.conflict_id}",
            conflict_id=row.conflict_id,
            classification=row.conflict_class,
            resolution_hint=classify_conflict_resolution_hint(row.conflict_class),
        )
        for row in build_conflict_inventory()
    ]
    return sorted(rows, key=lambda x: x.classification_id)
