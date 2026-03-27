from __future__ import annotations

from abx.failure.errorInventory import build_error_inventory


def build_error_taxonomy_records() -> tuple:
    return build_error_inventory()
