from __future__ import annotations

from abx.concurrency.conflictInventory import build_conflict_inventory
from abx.concurrency.types import MergeabilityRecord


def build_mergeability_records() -> list[MergeabilityRecord]:
    rows: list[MergeabilityRecord] = []
    for row in build_conflict_inventory():
        if row.conflict_class in {"NO_CONFLICT", "DUPLICATE_CONFLICT", "MERGEABLE_CONFLICT"}:
            merge_state = "MERGEABLE"
            reason = "compatible_or_duplicate_effect"
        elif row.conflict_class in {"TARGET_CONFLICT", "AUTHORITY_CONFLICT", "TEMPORAL_CONFLICT"}:
            merge_state = "SERIALIZE_INSTEAD"
            reason = "shared_target_or_scope_contention"
        else:
            merge_state = "NOT_MERGEABLE"
            reason = "safety_or_policy_block"
        rows.append(
            MergeabilityRecord(
                mergeability_id=f"merge.{row.conflict_id}",
                left_operation_id=row.left_operation_id,
                right_operation_id=row.right_operation_id,
                merge_state=merge_state,
                reason=reason,
            )
        )
    return sorted(rows, key=lambda x: x.mergeability_id)
