from __future__ import annotations

from abx.innovation.portfolioInventory import build_innovation_portfolio_inventory


def classify_innovation_portfolio() -> dict[str, list[str]]:
    buckets = {
        "active": [],
        "promising": [],
        "comparative": [],
        "stalled": [],
        "low_value": [],
        "retired": [],
        "archival": [],
    }
    for rec in build_innovation_portfolio_inventory():
        key = rec.portfolio_class
        buckets.setdefault(key, []).append(rec.experiment_id)
        if rec.relevance == "low" and rec.maintenance_burden == "high":
            buckets["low_value"].append(rec.experiment_id)
    for ids in buckets.values():
        ids.sort()
    return buckets


def detect_stale_experiment_drift() -> list[dict[str, str]]:
    stale: list[dict[str, str]] = []
    for rec in build_innovation_portfolio_inventory():
        if rec.portfolio_class == "stalled":
            stale.append(
                {
                    "experimentId": rec.experiment_id,
                    "reason": "stalled_portfolio_entry",
                }
            )
    return stale
