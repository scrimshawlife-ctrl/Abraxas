from __future__ import annotations

from itertools import combinations

from abx.concurrency.concurrentInventory import build_concurrent_operation_inventory
from abx.concurrency.types import ConflictRecord


def build_conflict_inventory() -> list[ConflictRecord]:
    rows: list[ConflictRecord] = []
    for left, right in combinations(build_concurrent_operation_inventory(), 2):
        if left.operation_id == right.operation_id:
            conflict_class = "DUPLICATE_CONFLICT"
        elif left.target_ref == right.target_ref and left.action_class != right.action_class:
            conflict_class = "TARGET_CONFLICT"
        elif left.domain_id == right.domain_id and left.authority_scope != right.authority_scope:
            conflict_class = "AUTHORITY_CONFLICT"
        elif left.side_effect_level == "HIGH" and right.side_effect_level == "HIGH" and left.domain_id == right.domain_id:
            conflict_class = "SIDE_EFFECT_CONFLICT"
        elif left.domain_id == right.domain_id and left.action_class == right.action_class == "WRITE":
            conflict_class = "TEMPORAL_CONFLICT"
        else:
            conflict_class = "NO_CONFLICT"
        phase = "PREFLIGHT" if conflict_class in {"TARGET_CONFLICT", "AUTHORITY_CONFLICT", "DUPLICATE_CONFLICT"} else "IN_FLIGHT"
        rows.append(
            ConflictRecord(
                conflict_id=f"conflict.{left.operation_id}.{right.operation_id}",
                left_operation_id=left.operation_id,
                right_operation_id=right.operation_id,
                conflict_class=conflict_class,
                phase=phase,
                evidence_ref=f"{left.target_ref}|{right.target_ref}",
            )
        )
    return sorted(rows, key=lambda x: x.conflict_id)
