from __future__ import annotations

from abx.lineage.lineageInventory import build_lineage_inventory


def build_lineage_records() -> tuple:
    return build_lineage_inventory()
