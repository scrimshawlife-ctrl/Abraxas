from __future__ import annotations

from abx.knowledge.knowledgeInventory import build_knowledge_inventory


def classify_knowledge_surfaces() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for row in build_knowledge_inventory():
        grouped.setdefault(row.classification, []).append(row.surface_id)
    return {k: sorted(v) for k, v in sorted(grouped.items())}
