from __future__ import annotations

from abx.productization.productInventory import build_product_surface_inventory


CLASSES = (
    "canonical_external",
    "semi_external_package",
    "experimental",
    "legacy",
    "deprecated_candidate",
    "internal_only",
)


def classify_product_surfaces() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in CLASSES}
    for row in build_product_surface_inventory():
        out[row.surface_class].append(row.surface_id)
    return {k: sorted(v) for k, v in out.items()}


def detect_duplicate_product_surfaces() -> list[str]:
    seen: set[tuple[str, str]] = set()
    dup: list[str] = []
    for row in build_product_surface_inventory():
        key = (row.capability, row.audience)
        if key in seen:
            dup.append(row.surface_id)
            continue
        seen.add(key)
    return sorted(dup)
