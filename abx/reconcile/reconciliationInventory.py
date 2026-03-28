from __future__ import annotations


def build_reconciliation_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("rec.001", "conf.001", "REFRESH_REPAIR", "RECONCILIATION_ELIGIBLE"),
        ("rec.002", "conf.002", "REFRESH_REPAIR", "RECONCILIATION_ELIGIBLE"),
        ("rec.003", "conf.003", "LAWFUL_MERGE", "RECONCILIATION_ELIGIBLE"),
        ("rec.004", "conf.004", "ROLLBACK_REPAIR", "RECONCILIATION_ELIGIBLE"),
        ("rec.005", "conf.005", "REBUILD_REPAIR", "RECONCILIATION_ELIGIBLE"),
        ("rec.006", "conf.006", "AUTHORITATIVE_OVERWRITE", "RECONCILIATION_ELIGIBLE"),
        ("rec.007", "conf.007", "QUARANTINE_REPAIR", "RECONCILIATION_ELIGIBLE"),
        ("rec.008", "conf.008", "REPAIR_LEGITIMACY_UNKNOWN", "NOT_COMPUTABLE"),
        ("rec.009", "conf.009", "REPAIR_FORBIDDEN", "RECONCILIATION_BLOCKED"),
        ("rec.010", "conf.010", "REPAIR_LEGITIMACY_UNKNOWN", "RECONCILIATION_PENDING"),
    )
