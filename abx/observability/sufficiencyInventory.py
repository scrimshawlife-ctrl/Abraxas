from __future__ import annotations


def build_sufficiency_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("suf.001", "runtime.latency.path", "SUFFICIENT_MEASUREMENT", "HIGH_CONSEQUENCE"),
        ("suf.002", "queue.retry.path", "PROVISIONALLY_SUFFICIENT", "MEDIUM_CONSEQUENCE"),
        ("suf.003", "identity.merge.path", "INSUFFICIENT_MEASUREMENT", "MEDIUM_CONSEQUENCE"),
        ("suf.004", "approval.override.path", "MEASUREMENT_AMBIGUOUS", "LOW_CONSEQUENCE"),
        ("suf.005", "capacity.exhaustion.path", "HIGH_CONSEQUENCE_UNDER_OBSERVED", "CRITICAL_CONSEQUENCE"),
        ("suf.006", "edge.delivery.path", "LOW_CONSEQUENCE_TOLERABLE_UNDER_MEASUREMENT", "LOW_CONSEQUENCE"),
        ("suf.007", "semantic.alias.path", "NOT_COMPUTABLE", "UNKNOWN"),
    )
