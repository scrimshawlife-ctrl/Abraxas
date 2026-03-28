from __future__ import annotations


def build_promotion_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("gate.001", "chg.feature.cache-refresh", "PROMOTION_CANDIDATE", "cross-layer checks queued"),
        ("gate.002", "chg.patch.semantic-fix", "PROMOTION_GATED", "awaiting evidence threshold"),
        ("gate.003", "chg.fix.identity-merge", "PROMOTION_APPROVED", "identity+lineage checks passed"),
        ("gate.004", "chg.exp.proto-ui", "PROMOTION_FAILED_GATE", "semantic mismatch unresolved"),
        ("gate.005", "chg.hotfix.runtime", "PROMOTION_DEFERRED", "rollback blast radius unclear"),
        ("gate.006", "chg.migrate.schema", "NOT_COMPUTABLE", "missing replay evidence"),
    )
