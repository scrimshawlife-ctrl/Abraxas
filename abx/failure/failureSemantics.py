from __future__ import annotations

from abx.failure.types import FailureSemanticRecord


def build_failure_semantic_inventory() -> tuple[FailureSemanticRecord, ...]:
    return (
        FailureSemanticRecord("sem.net.timeout", "err.net.timeout", "RETRYABLE_FAILURE", "DEGRADED_BUT_OPERABLE", "LOW"),
        FailureSemanticRecord("sem.db.schema", "err.db.schema", "NON_RETRYABLE_FAILURE", "DEGRADED_AND_UNSAFE", "MEDIUM"),
        FailureSemanticRecord("sem.cache.corrupt", "err.cache.corrupt", "NON_RETRYABLE_FAILURE", "DEGRADED_AND_UNSAFE", "HIGH"),
        FailureSemanticRecord("sem.dep.auth", "err.dep.auth", "RETRYABLE_FAILURE", "DEGRADED_BUT_OPERABLE", "MEDIUM"),
        FailureSemanticRecord("sem.orch.invalid", "err.orch.invalid", "HUMAN_INTERVENTION_REQUIRED", "DEGRADED_AND_UNSAFE", "MEDIUM"),
    )
