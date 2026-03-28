from __future__ import annotations

from abx.freshness.horizonInventory import build_horizon_inventory


def build_time_horizon_records() -> tuple:
    return build_horizon_inventory()
