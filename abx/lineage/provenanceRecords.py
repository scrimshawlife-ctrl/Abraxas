from __future__ import annotations

from abx.lineage.provenanceInventory import build_provenance_inventory


def build_provenance_records() -> tuple:
    return build_provenance_inventory()
