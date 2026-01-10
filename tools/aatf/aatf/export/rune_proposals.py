from __future__ import annotations

from typing import Any, Dict, List

from ..provenance import sha256_hex
from ..storage import list_queue_items


def export_rune_proposals() -> Dict[str, Any]:
    proposals: List[Dict[str, Any]] = []
    for item in [i for i in list_queue_items() if i.get("state") in {"APPROVED", "EXPORTED"}]:
        proposals.append(
            {
                "proposal_id": sha256_hex(f"rune:{item['item_id']}")[:16],
                "rune_name": f"Rune_{item['item_id'][:6]}",
                "glyph_ref": None,
                "semantics": "Shadow-only training rune proposal",
                "oppositions": [],
                "activation_conditions": ["manual approval"],
                "deactivation_conditions": ["governance reject"],
                "mapping": {"codepoint": None, "deck": None},
                "provenance": {
                    "source_ids": [item["source_hash"]],
                    "created_at": "1970-01-01T00:00:00Z",
                },
            }
        )

    return {"proposals": proposals}
