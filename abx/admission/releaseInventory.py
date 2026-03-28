from __future__ import annotations


def build_release_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("rel.001", "chg.feature.cache-refresh", "RELEASE_PROVISIONAL", "freshness validation pending"),
        ("rel.002", "chg.patch.semantic-fix", "EXPERIMENTAL", "canary only"),
        ("rel.003", "chg.fix.identity-merge", "RELEASE_READY", "all governing surfaces coherent"),
        ("rel.004", "chg.exp.proto-ui", "RELEASE_BLOCKED", "promotion failed"),
        ("rel.005", "chg.hotfix.runtime", "ROLLBACK_REQUIRED", "integrity confidence degraded"),
        ("rel.006", "chg.migrate.schema", "NOT_COMPUTABLE", "release evidence unavailable"),
    )
