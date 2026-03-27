from __future__ import annotations

from abx.knowledge.continuityInventory import build_continuity_inventory


def normalize_continuity_refs(run_id: str = "RUN-CONTINUITY") -> list[dict[str, str | None]]:
    rows = []
    for row in build_continuity_inventory(run_id=run_id):
        rows.append(
            {
                "continuity_id": row.continuity_id,
                "run_id": row.run_id.strip().upper(),
                "previous_ref": row.previous_ref,
                "baseline_ref": row.baseline_ref,
                "incident_ref": row.incident_ref,
                "linkage_type": row.linkage_type,
            }
        )
    return sorted(rows, key=lambda x: str(x["continuity_id"]))
