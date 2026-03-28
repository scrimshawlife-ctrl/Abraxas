from __future__ import annotations

from abx.explanation.boundaryInventory import build_boundary_inventory, build_layer_inventory


def build_explanation_boundary_records() -> tuple:
    return build_boundary_inventory()


def build_explanation_layer_records() -> tuple:
    return build_layer_inventory()
