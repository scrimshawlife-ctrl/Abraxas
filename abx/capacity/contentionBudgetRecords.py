from __future__ import annotations

from abx.capacity.contentionInventory import build_contention_inventory
from abx.capacity.types import ContentionBudgetRecord, OvercommitmentRecord, StarvationRiskRecord


def build_contention_budget_records() -> list[ContentionBudgetRecord]:
    return [
        ContentionBudgetRecord(budget_id=bid, resource_ref=resource_ref, contention_state=state, budget_state=budget)
        for bid, resource_ref, state, budget in build_contention_inventory()
    ]


def build_overcommitment_records() -> list[OvercommitmentRecord]:
    return [
        OvercommitmentRecord("ovr.001", "operator.oncall.eu", "OVERCOMMITTED", "hard and soft commitments overlap"),
        OvercommitmentRecord("ovr.002", "queue.ingest.high", "NEAR_OVERCOMMIT", "burstable limits near ceiling"),
    ]


def build_starvation_risk_records() -> list[StarvationRiskRecord]:
    return [
        StarvationRiskRecord("str.001", "bandwidth.edge.link", "STARVATION_RISK", "best-effort flows starved by guarantees"),
        StarvationRiskRecord("str.002", "token.llm.tier1", "STARVATION_ACTIVE", "budget exhausted and retries blocked"),
    ]
