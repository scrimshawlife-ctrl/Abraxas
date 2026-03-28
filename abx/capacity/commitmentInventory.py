from __future__ import annotations


def build_commitment_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("com.001", "compute.pool.alpha", "HARD_CAPACITY_COMMITTED", "latency SLO guarantee"),
        ("com.002", "queue.ingest.high", "SOFT_CAPACITY_COMMITTED", "best effort priority"),
        ("com.003", "token.llm.tier1", "BEST_EFFORT_CLAIM", "non-critical workload"),
        ("com.004", "operator.oncall.eu", "COMMITMENT_UNKNOWN", "handoff pending"),
        ("com.005", "bandwidth.edge.link", "BLOCKED", "quota exhausted"),
        ("com.006", "gpu.batch.pool", "NOT_COMPUTABLE", "capacity feed unavailable"),
    )


def build_allocation_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("all.001", "compute.pool.alpha", "ALLOCATED", "reserved compute assigned"),
        ("all.002", "queue.ingest.high", "ALLOCATED", "queue partition assigned"),
        ("all.003", "token.llm.tier1", "UNALLOCATED", "best effort not granted"),
        ("all.004", "operator.oncall.eu", "UNALLOCATED", "schedule unresolved"),
        ("all.005", "bandwidth.edge.link", "UNALLOCATED", "blocked by contention"),
        ("all.006", "gpu.batch.pool", "NOT_COMPUTABLE", "allocator telemetry missing"),
    )
