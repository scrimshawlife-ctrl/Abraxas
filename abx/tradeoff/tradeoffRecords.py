from __future__ import annotations

from abx.tradeoff.tradeoffInventory import build_objective_conflict_inventory, build_sacrifice_inventory, build_tradeoff_inventory


def build_tradeoff_records() -> tuple:
    return build_tradeoff_inventory()


def build_sacrifice_records() -> tuple:
    return build_sacrifice_inventory()


def build_objective_conflict_records() -> tuple:
    return build_objective_conflict_inventory()
