from __future__ import annotations

from abx.freshness.stalenessInventory import build_staleness_inventory


def build_staleness_records() -> tuple:
    return build_staleness_inventory()
