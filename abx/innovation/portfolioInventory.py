from __future__ import annotations

from abx.innovation.types import InnovationPortfolioRecord


def build_innovation_portfolio_inventory() -> list[InnovationPortfolioRecord]:
    return [
        InnovationPortfolioRecord(
            portfolio_id="port-routing",
            experiment_id="exp-hypothesis-routing-v2",
            portfolio_class="promising",
            relevance="high",
            maintenance_burden="low",
            promotion_potential="high",
        ),
        InnovationPortfolioRecord(
            portfolio_id="port-latency",
            experiment_id="exp-latency-compression-3",
            portfolio_class="comparative",
            relevance="high",
            maintenance_burden="medium",
            promotion_potential="medium",
        ),
        InnovationPortfolioRecord(
            portfolio_id="port-memory",
            experiment_id="exp-symbolic-memory-bridge",
            portfolio_class="active",
            relevance="medium",
            maintenance_burden="medium",
            promotion_potential="low",
        ),
        InnovationPortfolioRecord(
            portfolio_id="port-legacy",
            experiment_id="exp-legacy-shadow-parser",
            portfolio_class="stalled",
            relevance="low",
            maintenance_burden="high",
            promotion_potential="low",
        ),
    ]
