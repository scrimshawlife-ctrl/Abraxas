from __future__ import annotations


def build_contention_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("bud.001", "compute.pool.alpha", "CONTENTION_TOLERABLE", "BUDGET_HEALTHY"),
        ("bud.002", "queue.ingest.high", "CONTENTION_ACTIVE", "BUDGET_DEGRADING"),
        ("bud.003", "token.llm.tier1", "CONTENTION_BLOCKING", "BUDGET_EXHAUSTED"),
        ("bud.004", "operator.oncall.eu", "OVERCOMMITTED", "BUDGET_EXHAUSTED"),
        ("bud.005", "bandwidth.edge.link", "STARVATION_RISK", "BUDGET_DEGRADING"),
        ("bud.006", "gpu.batch.pool", "NOT_COMPUTABLE", "UNKNOWN"),
    )
