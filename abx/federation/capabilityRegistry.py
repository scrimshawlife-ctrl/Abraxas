from __future__ import annotations

from abx.federation.capabilityInventory import build_capability_inventory


def capability_registry_summary() -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for row in build_capability_inventory():
        owners.setdefault(row.owner, []).append(row.capability_id)
    return {k: sorted(v) for k, v in sorted(owners.items())}
