from __future__ import annotations


def build_rejection_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("rej.001", "chg.exp.proto-ui", "REJECTED", "failed semantic and UX gates"),
        ("rej.002", "chg.patch.semantic-fix", "DEFERRED", "evidence threshold unmet"),
        ("rej.003", "chg.migrate.schema", "RE_ADMISSION_REQUIRED", "lineage replay incomplete"),
    )


def build_rollback_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("rbk.001", "chg.hotfix.runtime", "ROLLBACK_TRIGGERED", "integrity drift detected"),
        ("rbk.002", "chg.fix.identity-merge", "ROLLBACK_COMPLETE", "candidate safely reverted in staging"),
        ("rbk.003", "chg.migrate.schema", "RE_ADMISSION_REQUIRED", "rollback blocked until schema baseline restored"),
    )
