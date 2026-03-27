from __future__ import annotations

from abx.innovation.portfolioInventory import build_innovation_portfolio_inventory
from abx.innovation.types import RetirementRecord


def build_retirement_records() -> list[RetirementRecord]:
    records: list[RetirementRecord] = []
    for rec in build_innovation_portfolio_inventory():
        if rec.portfolio_class == "stalled" or (rec.relevance == "low" and rec.maintenance_burden == "high"):
            records.append(
                RetirementRecord(
                    retirement_id=f"retire-{rec.experiment_id}",
                    experiment_id=rec.experiment_id,
                    recommendation="retire",
                    reason="low_signal_high_burden",
                    archive_ref=f"archive:{rec.experiment_id}",
                )
            )
    return records
