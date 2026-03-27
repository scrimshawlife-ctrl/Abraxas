from __future__ import annotations

from abx.failure.types import FailureTransitionRecord


def build_failure_transition_records() -> tuple[FailureTransitionRecord, ...]:
    return (
        FailureTransitionRecord("tr.fail.001", "err.net.timeout", "RETRY_ALLOWED", "RECOVERY_ELIGIBLE", "dependency_restored"),
        FailureTransitionRecord("tr.fail.002", "err.db.schema", "RETRY_ALLOWED", "RETRY_FORBIDDEN", "persistent_signature_detected"),
        FailureTransitionRecord("tr.fail.003", "err.cache.corrupt", "DEGRADED_OPERATION", "QUARANTINE_REQUIRED", "integrity_check_failed"),
        FailureTransitionRecord("tr.fail.004", "err.cache.corrupt", "QUARANTINE_REQUIRED", "REBUILD_REQUIRED", "state_not_salvageable"),
        FailureTransitionRecord("tr.fail.005", "err.dep.auth", "DEGRADED_OPERATION", "ROLLBACK_REQUIRED", "unsafe_restoration_risk"),
    )
