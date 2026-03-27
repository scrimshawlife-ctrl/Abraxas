from __future__ import annotations

from abx.docs_governance.freshnessInventory import build_freshness_inventory


def classify_freshness_states() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {
        "fresh": [],
        "monitored": [],
        "stale_candidate": [],
        "archival": [],
        "deprecated": [],
    }
    for row in build_freshness_inventory():
        out[row.freshness_state if row.freshness_state in out else "monitored"].append(row.freshness_id)
    return {k: sorted(v) for k, v in out.items()}
