from __future__ import annotations

from abx.lineage.mutationInventory import build_mutation_inventory


def build_mutation_legitimacy_records() -> tuple:
    return build_mutation_inventory()
