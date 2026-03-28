from __future__ import annotations

from abx.operator.interventionInventory import build_intervention_inventory


def build_manual_intervention_records() -> tuple:
    return build_intervention_inventory()
