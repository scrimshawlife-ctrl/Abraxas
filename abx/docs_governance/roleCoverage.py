from __future__ import annotations

from abx.docs_governance.roleInventory import build_role_inventory


def classify_role_legibility() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"fully_legible": [], "partial": [], "fragmented": [], "legacy": [], "not_computable": []}
    for row in build_role_inventory():
        key = row.coverage_state if row.coverage_state in out else "not_computable"
        out[key].append(row.role_id)
    return {k: sorted(v) for k, v in out.items()}
