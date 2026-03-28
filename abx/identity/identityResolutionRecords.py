from __future__ import annotations

from abx.identity.identityInventory import build_identity_inventory


def build_identity_resolution_records() -> tuple:
    return build_identity_inventory()
