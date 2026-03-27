from __future__ import annotations

from abx.epistemics.validationInventory import build_validation_surface_inventory


def build_validation_ownership() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in build_validation_surface_inventory():
        out.setdefault(row.owner, []).append(row.validation_id)
    return {k: sorted(v) for k, v in sorted(out.items())}
