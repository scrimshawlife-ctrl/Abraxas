from __future__ import annotations

from abx.freshness.freshnessInventory import build_decay_inventory, build_freshness_inventory


def build_freshness_records() -> tuple:
    return build_freshness_inventory()


def build_decay_records() -> tuple:
    return build_decay_inventory()
