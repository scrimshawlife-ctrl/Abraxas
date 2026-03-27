from __future__ import annotations

from abx.failure.types import RecoveryActionRecord


def build_recovery_action_records() -> tuple[RecoveryActionRecord, ...]:
    return (
        RecoveryActionRecord("act.net.timeout", "err.net.timeout", "RETRY_ALLOWED", "transient_boundary_failure"),
        RecoveryActionRecord("act.db.schema", "err.db.schema", "ROLLBACK_REQUIRED", "schema_mismatch"),
        RecoveryActionRecord("act.cache.corrupt", "err.cache.corrupt", "REBUILD_REQUIRED", "integrity_loss"),
        RecoveryActionRecord("act.dep.auth", "err.dep.auth", "QUARANTINE_REQUIRED", "dependency_not_cleared"),
        RecoveryActionRecord("act.orch.invalid", "err.orch.invalid", "MANUAL_REPAIR_REQUIRED", "invalid_state_machine"),
    )
