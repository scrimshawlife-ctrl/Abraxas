from __future__ import annotations


def build_effect_realization_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("real.001", "act.deploy.schema-v2", "EFFECT_OBSERVED", "DIRECT_OBSERVATION"),
        ("real.002", "act.notify.partner", "EFFECT_ACKNOWLEDGED", "DOWNSTREAM_ACK"),
        ("real.003", "act.repair.cache", "EFFECT_INFERRED", "CORRELATED_METRICS"),
        ("real.004", "act.cleanup.tmp", "EFFECT_UNVERIFIED", "ASSUMED"),
        ("real.005", "act.run.canary", "VERIFICATION_REQUIRED", "PARTIAL_SIGNAL"),
        ("real.006", "act.migrate.legacy", "NOT_COMPUTABLE", "MISSING_EVIDENCE"),
    )
