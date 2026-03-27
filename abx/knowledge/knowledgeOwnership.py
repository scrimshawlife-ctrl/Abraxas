from __future__ import annotations

from abx.knowledge.knowledgeInventory import build_knowledge_inventory


def knowledge_ownership_report() -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for row in build_knowledge_inventory():
        owners.setdefault(row.owner, []).append(row.surface_id)
    return {owner: sorted(surfaces) for owner, surfaces in sorted(owners.items())}
