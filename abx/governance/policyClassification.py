from __future__ import annotations

from abx.governance.policyInventory import build_policy_inventory


def classify_policy_surfaces() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for row in build_policy_inventory():
        grouped.setdefault(row.classification, []).append(row.policy_id)
    return {k: sorted(v) for k, v in sorted(grouped.items())}


def detect_duplicate_policy_surfaces() -> list[str]:
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for row in build_policy_inventory():
        if row.surface in seen:
            duplicates.append(f"{seen[row.surface]}::{row.policy_id}")
        else:
            seen[row.surface] = row.policy_id
    return sorted(duplicates)
