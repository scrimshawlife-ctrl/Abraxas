from __future__ import annotations

from abx.failure.types import RecoveryEligibilityRecord


def build_recovery_eligibility_inventory() -> tuple[RecoveryEligibilityRecord, ...]:
    return (
        RecoveryEligibilityRecord("elig.net.timeout", "err.net.timeout", "YES", "YES", "NO"),
        RecoveryEligibilityRecord("elig.db.schema", "err.db.schema", "NO", "NO", "YES"),
        RecoveryEligibilityRecord("elig.cache.corrupt", "err.cache.corrupt", "NO", "NO", "YES"),
        RecoveryEligibilityRecord("elig.dep.auth", "err.dep.auth", "YES", "PARTIAL", "YES"),
        RecoveryEligibilityRecord("elig.orch.invalid", "err.orch.invalid", "NO", "NO", "YES"),
    )
