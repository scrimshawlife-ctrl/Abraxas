from __future__ import annotations

from abx.failure.failureSemantics import build_failure_semantic_inventory
from abx.failure.types import RecoverabilityRecord


def build_recoverability_records() -> tuple[RecoverabilityRecord, ...]:
    return tuple(
        RecoverabilityRecord(
            recoverability_id=f"rec.{row.semantic_id}",
            semantic_id=row.semantic_id,
            retryability="RETRY_ALLOWED" if row.recoverability == "RETRYABLE_FAILURE" else "RETRY_FORBIDDEN",
            human_intervention="REQUIRED" if row.recoverability == "HUMAN_INTERVENTION_REQUIRED" else "OPTIONAL",
        )
        for row in build_failure_semantic_inventory()
    )
