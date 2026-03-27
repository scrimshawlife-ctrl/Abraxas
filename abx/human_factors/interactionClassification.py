from __future__ import annotations

from abx.human_factors.interactionInventory import build_interaction_inventory


SURFACE_CLASSES = (
    "primary",
    "secondary",
    "drilldown",
    "contextual_only",
    "redundant",
    "legacy_deprecated_candidate",
)


def classify_interaction_surfaces() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in SURFACE_CLASSES}
    for row in build_interaction_inventory():
        out[row.surface_class].append(row.surface_id)
    return {k: sorted(v) for k, v in out.items()}


def detect_duplicate_interaction_surfaces() -> list[str]:
    seen: set[tuple[str, str]] = set()
    dup: list[str] = []
    for row in build_interaction_inventory():
        key = (row.task_type, row.workflow_phase)
        if key in seen:
            dup.append(row.surface_id)
            continue
        seen.add(key)
    return sorted(dup)
