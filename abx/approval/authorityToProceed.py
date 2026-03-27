from __future__ import annotations

from abx.approval.authorityInventory import build_authority_inventory


def build_authority_to_proceed_records() -> tuple:
    return build_authority_inventory()
