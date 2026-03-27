from __future__ import annotations

from abx.observability.surfaceInventory import build_surface_inventory


def classify_surfaces() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for row in build_surface_inventory():
        grouped.setdefault(row.category, []).append(row.surface_id)
    return {k: sorted(v) for k, v in sorted(grouped.items())}


def detect_redundant_surfaces() -> list[str]:
    rows = build_surface_inventory()
    by_source: dict[str, list[str]] = {}
    for row in rows:
        by_source.setdefault(row.source, []).append(row.surface_id)
    redundant = []
    for source, surfaces in sorted(by_source.items()):
        if len(surfaces) > 1:
            redundant.append(f"{source}:{','.join(sorted(surfaces))}")
    return redundant
