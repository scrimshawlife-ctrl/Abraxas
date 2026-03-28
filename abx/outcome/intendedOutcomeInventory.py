from __future__ import annotations


def build_intended_outcome_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("out.001", "act.deploy.schema-v2", "INTENDED_EFFECT", "runtime_behavior"),
        ("out.002", "act.notify.partner", "DOWNSTREAM_EFFECT", "partner_ack"),
        ("out.003", "act.repair.cache", "INTENDED_EFFECT", "cache_consistency"),
        ("out.004", "act.cleanup.tmp", "NO_EFFECT_EXPECTED", "maintenance"),
        ("out.005", "act.run.canary", "SIDE_EFFECT", "telemetry"),
        ("out.006", "act.migrate.legacy", "OUTCOME_UNKNOWN", "unknown"),
    )
