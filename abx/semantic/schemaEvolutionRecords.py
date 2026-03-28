from __future__ import annotations

from abx.semantic.schemaEvolutionInventory import build_schema_evolution_inventory


def build_schema_evolution_records() -> tuple:
    return build_schema_evolution_inventory()
