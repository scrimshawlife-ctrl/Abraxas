from __future__ import annotations

from abx.productization.audienceInventory import build_audience_inventory


def classify_audience_legibility() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"fully_legible": [], "partial": [], "fragmented": [], "legacy": [], "not_computable": []}
    for row in build_audience_inventory():
        key = row.legibility_state if row.legibility_state in out else "not_computable"
        out[key].append(row.audience_id)
    return {k: sorted(v) for k, v in out.items()}
