from __future__ import annotations

from abx.productization.productInventory import build_product_surface_inventory


def build_product_ownership() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in build_product_surface_inventory():
        out.setdefault(row.owner, []).append(row.surface_id)
    return {k: sorted(v) for k, v in sorted(out.items())}
