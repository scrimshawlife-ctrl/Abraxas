from __future__ import annotations

from abx.performance.performanceInventory import build_performance_surface_inventory


def build_performance_ownership() -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for record in build_performance_surface_inventory():
        owners.setdefault(record.owner, []).append(record.surface_id)
    return {k: sorted(v) for k, v in sorted(owners.items())}
