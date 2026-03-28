from __future__ import annotations

from abx.capacity.types import BudgetExhaustionRecord, CapacityTransitionRecord


def build_capacity_transition_records() -> list[CapacityTransitionRecord]:
    return [
        CapacityTransitionRecord("ctr.001", "compute.pool.alpha", "RESOURCE_AVAILABLE", "RESOURCE_RESERVED", "hard reservation activated"),
        CapacityTransitionRecord("ctr.002", "queue.ingest.high", "RESOURCE_RESERVED", "RESOURCE_ALLOCATED", "allocation granted"),
        CapacityTransitionRecord("ctr.003", "token.llm.tier1", "PROVISIONAL_HOLD_ACTIVE", "BUDGET_EXHAUSTED", "token budget depleted"),
        CapacityTransitionRecord("ctr.004", "operator.oncall.eu", "SOFT_CAPACITY_COMMITTED", "GUARANTEE_DOWNGRADED", "soft commitment preempted"),
        CapacityTransitionRecord("ctr.005", "bandwidth.edge.link", "RESOURCE_RESERVED", "RELEASE_REQUIRED", "contention threshold exceeded"),
        CapacityTransitionRecord("ctr.006", "gpu.batch.pool", "RESOURCE_RESERVED", "ADMISSION_BLOCKED", "unknown capacity state"),
    ]


def build_budget_exhaustion_records() -> list[BudgetExhaustionRecord]:
    return [
        BudgetExhaustionRecord("exh.001", "token.llm.tier1", "BUDGET_EXHAUSTED", "tokens consumed by higher-priority workload"),
        BudgetExhaustionRecord("exh.002", "operator.oncall.eu", "TRUST_DOWNGRADED", "operator attention budget violated"),
    ]
