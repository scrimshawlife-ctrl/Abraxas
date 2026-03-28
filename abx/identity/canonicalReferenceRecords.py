from __future__ import annotations

from abx.identity.persistenceInventory import build_canonical_reference_inventory, build_persistence_inventory


def build_entity_persistence_records() -> tuple:
    return build_persistence_inventory()


def build_canonical_reference_records() -> tuple:
    return build_canonical_reference_inventory()
