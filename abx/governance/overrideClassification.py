from __future__ import annotations

from abx.governance.overrideInventory import build_override_inventory


def classify_overrides() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for row in build_override_inventory():
        grouped.setdefault(row.override_type, []).append(row.override_id)
    return {k: sorted(v) for k, v in sorted(grouped.items())}


def detect_stale_overrides() -> list[str]:
    stale = [row.override_id for row in build_override_inventory() if row.duration == "permanent"]
    return sorted(stale)
