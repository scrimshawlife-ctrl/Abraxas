from __future__ import annotations

from abx.federation.interopInventory import build_interop_inventory


def classify_interop_paths() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for row in build_interop_inventory():
        grouped.setdefault(row.classification, []).append(row.interop_id)
    return {k: sorted(v) for k, v in sorted(grouped.items())}


def detect_redundant_interop_patterns() -> list[str]:
    seen: dict[tuple[str, str], str] = {}
    dupes: list[str] = []
    for row in build_interop_inventory():
        key = (row.producer_module, row.consumer_module)
        if key in seen:
            dupes.append(f"{seen[key]}::{row.interop_id}")
        else:
            seen[key] = row.interop_id
    return sorted(dupes)
