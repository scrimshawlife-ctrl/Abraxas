from __future__ import annotations

from typing import Any, Dict, List

from ..provenance import sha256_hex
from ..storage import list_queue_items


def export_neon_genie() -> Dict[str, Any]:
    apps: List[Dict[str, Any]] = []
    for item in [i for i in list_queue_items() if i.get("state") in {"APPROVED", "EXPORTED"}]:
        apps.append(
            {
                "id": sha256_hex(f"neon:{item['item_id']}")[:16],
                "name": f"Forge App {item['item_id'][:6]}",
                "novelty_claim": "Deterministic training artifact review",
                "why_now": "Shadow-only governance demand",
                "category_tags": item.get("tags", []),
                "violates_existing_systems": False,
                "differentiation": "Local-only, deterministic provenance",
                "vc_gap_hypothesis": "Governed training pipelines",
                "risk_notes": "Manual review required",
                "build_vector": {
                    "complexity_estimate": "medium",
                    "time_estimate": "2-4 weeks",
                    "compute_estimate": "low",
                },
                "provenance": {
                    "source_ids": [item["source_hash"]],
                    "created_at": "1970-01-01T00:00:00Z",
                },
            }
        )

    return {
        "run_id": sha256_hex("neon_genie")[:16],
        "date": "1970-01-01",
        "apps": apps,
    }
