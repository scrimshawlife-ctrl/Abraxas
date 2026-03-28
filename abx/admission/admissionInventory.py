from __future__ import annotations


def build_admission_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("adm.001", "chg.feature.cache-refresh", "CHANGE_PROPOSED", "EVIDENCE_PARTIAL"),
        ("adm.002", "chg.patch.semantic-fix", "ADMISSION_PENDING", "EVIDENCE_PENDING"),
        ("adm.003", "chg.fix.identity-merge", "ADMISSION_APPROVED", "EVIDENCE_SUFFICIENT"),
        ("adm.004", "chg.exp.proto-ui", "ADMISSION_REJECTED", "EVIDENCE_CONFLICTED"),
        ("adm.005", "chg.hotfix.runtime", "ADMISSION_BLOCKED", "EVIDENCE_INTEGRITY_RISK"),
        ("adm.006", "chg.migrate.schema", "NOT_COMPUTABLE", "EVIDENCE_NOT_COMPUTABLE"),
    )
