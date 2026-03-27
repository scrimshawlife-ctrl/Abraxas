from __future__ import annotations

from abx.meta.canonInventory import build_canon_surface_inventory


def build_canon_ownership_map() -> dict[str, str]:
    return {rec.canon_id: rec.owner for rec in build_canon_surface_inventory()}


def detect_unowned_canon_surfaces() -> list[str]:
    return sorted(rec.canon_id for rec in build_canon_surface_inventory() if rec.owner in {"", "unknown"})
