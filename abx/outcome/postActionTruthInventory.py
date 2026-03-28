from __future__ import annotations


def build_post_action_truth_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("truth.001", "act.deploy.schema-v2", "FULL_REALIZED_OUTCOME", "direct observation matched expected behavior"),
        ("truth.002", "act.notify.partner", "DELAYED_OUTCOME", "ack arrived but downstream processing lagging"),
        ("truth.003", "act.repair.cache", "PARTIAL_REALIZED_OUTCOME", "cache coherent for subset"),
        ("truth.004", "act.cleanup.tmp", "ABSENT_OUTCOME", "no evidence action effect occurred"),
        ("truth.005", "act.run.canary", "CONTRADICTORY_OUTCOME", "telemetry conflicts with completion logs"),
        ("truth.006", "act.migrate.legacy", "BLOCKED", "verification pipeline unavailable"),
    )


def build_contradictory_outcome_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("con.001", "act.run.canary", "CONTRADICTORY_EVIDENCE_ACTIVE", "control and treatment disagree"),
        ("con.002", "act.cleanup.tmp", "SPOOF_RISK_ACTIVE", "untrusted source reported success"),
        ("con.003", "act.migrate.legacy", "REVERIFICATION_REQUIRED", "evidence timestamp invalid"),
    )
