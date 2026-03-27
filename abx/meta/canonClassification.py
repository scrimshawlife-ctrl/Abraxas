from __future__ import annotations

from abx.meta.canonInventory import build_canon_surface_inventory


CANON_CLASSES = {
    "authoritative-canon",
    "governed-derived-reference",
    "shadow-candidate",
    "superseded-canon",
    "legacy-residue",
    "deprecated-candidate",
}


def classify_canon_surfaces() -> dict[str, list[str]]:
    buckets = {
        "authoritative_canon": [],
        "governed_derived_reference": [],
        "shadow_candidate": [],
        "superseded_canon": [],
        "legacy_residue": [],
        "deprecated_candidate": [],
    }
    for rec in build_canon_surface_inventory():
        key = rec.canon_class.replace("-", "_")
        buckets.setdefault(key, []).append(rec.canon_id)
    for ids in buckets.values():
        ids.sort()
    return buckets


def detect_duplicate_canon_home() -> list[dict[str, str]]:
    seen: dict[str, str] = {}
    issues: list[dict[str, str]] = []
    for rec in build_canon_surface_inventory():
        if rec.surface_ref in seen:
            issues.append({"canonId": rec.canon_id, "reason": "duplicate_home", "surfaceRef": rec.surface_ref})
        else:
            seen[rec.surface_ref] = rec.canon_id
    return issues


def detect_canon_taxonomy_drift() -> list[dict[str, str]]:
    drift: list[dict[str, str]] = []
    for rec in build_canon_surface_inventory():
        if rec.canon_class not in CANON_CLASSES:
            drift.append({"canonId": rec.canon_id, "reason": "unknown_canon_class", "canonClass": rec.canon_class})
    return drift
