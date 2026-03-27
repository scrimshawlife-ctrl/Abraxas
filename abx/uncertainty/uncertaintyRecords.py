from __future__ import annotations

from abx.uncertainty.uncertaintyInventory import build_uncertainty_inventory


def build_uncertainty_records() -> tuple:
    return build_uncertainty_inventory()
