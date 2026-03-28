from __future__ import annotations


def build_resource_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("resv.001", "compute.pool.alpha", "RESOURCE_AVAILABLE", "actor.scheduler"),
        ("resv.002", "queue.ingest.high", "RESOURCE_RESERVED", "actor.pipeline"),
        ("resv.003", "token.llm.tier1", "PROVISIONAL_HOLD_ACTIVE", "actor.planner"),
        ("resv.004", "operator.oncall.eu", "RESERVATION_EXPIRED", "actor.obligation"),
        ("resv.005", "bandwidth.edge.link", "RESERVATION_DENIED", "actor.sync"),
        ("resv.006", "gpu.batch.pool", "NOT_COMPUTABLE", "actor.runtime"),
    )
