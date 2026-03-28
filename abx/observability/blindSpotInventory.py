from __future__ import annotations


def build_blind_spot_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("bs.001", "queue.retry.path", "BLIND_SPOT_SUSPECTED", "MEDIUM"),
        ("bs.002", "identity.merge.path", "BLIND_SPOT_CONFIRMED", "HIGH"),
        ("bs.003", "approval.override.path", "BLIND_SPOT_HIGH_RISK", "CRITICAL"),
        ("bs.004", "runtime.latency.path", "BLIND_SPOT_TOLERABLE", "LOW"),
        ("bs.005", "edge.delivery.path", "BLIND_SPOT_BLOCKED", "CRITICAL"),
        ("bs.006", "capacity.exhaustion.path", "NOT_COMPUTABLE", "UNKNOWN"),
    )
