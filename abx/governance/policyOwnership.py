from __future__ import annotations

from abx.governance.policyInventory import build_policy_inventory


def policy_ownership_report() -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for row in build_policy_inventory():
        owners.setdefault(row.owner, []).append(row.policy_id)
    return {owner: sorted(items) for owner, items in sorted(owners.items())}
