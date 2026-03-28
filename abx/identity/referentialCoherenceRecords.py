from __future__ import annotations

from abx.identity.coherenceInventory import build_alias_inventory, build_coherence_inventory, build_merge_inventory, build_split_inventory


def build_referential_coherence_records() -> tuple:
    return build_coherence_inventory()


def build_alias_records() -> tuple:
    return build_alias_inventory()


def build_merge_records() -> tuple:
    return build_merge_inventory()


def build_split_records() -> tuple:
    return build_split_inventory()
