from __future__ import annotations

from typing import Any, Dict, List

from ..provenance import sha256_hex
from ..storage import list_queue_items, load_blob


def export_aalmanac() -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    for item in [i for i in list_queue_items() if i.get("state") in {"APPROVED", "EXPORTED"}]:
        blob = load_blob(item["content_id"])
        canonical = blob.get("canonical_text", "")
        tokens = canonical.split()
        term = tokens[0] if tokens else "unknown"
        term_type = "single" if " " not in term else "compound"
        entry = {
            "id": sha256_hex(f"aalmanac:{item['item_id']}")[:16],
            "term_type": term_type,
            "term": term,
            "context_shift": canonical[:160],
            "domain_tags": item.get("tags", []),
            "signals": {
                "novelty_score": 0.5,
                "adoption_pressure": 0.5,
                "drift_charge": 0.3,
            },
            "provenance": {
                "source_ids": [item["source_hash"]],
                "created_at": "1970-01-01T00:00:00Z",
            },
        }
        entries.append(entry)
    return {"entries": entries}
