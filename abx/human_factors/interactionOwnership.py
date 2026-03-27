from __future__ import annotations

from abx.human_factors.interactionInventory import build_interaction_inventory


def build_interaction_ownership() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in build_interaction_inventory():
        out.setdefault(row.owner, []).append(row.surface_id)
    return {k: sorted(v) for k, v in sorted(out.items())}
