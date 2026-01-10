from __future__ import annotations

from typing import Dict

from ..provenance import sha256_hex
from ..storage import append_ledger, update_queue_state
from .states import QueueState


def apply_review(item_id: str, decision: QueueState, notes: str) -> Dict[str, str]:
    if decision not in {QueueState.APPROVED, QueueState.REJECTED}:
        raise ValueError("Decision must be APPROVED or REJECTED")
    updated = update_queue_state(item_id, {"state": decision.value, "review_notes": notes})
    if not updated:
        raise ValueError("Queue item not found")
    review_id = sha256_hex(f"review:{item_id}:{decision.value}:{notes}")
    append_ledger("REVIEWED", {"item_id": item_id, "decision": decision.value, "notes": notes, "review_id": review_id})
    return {"item_id": item_id, "decision": decision.value, "review_id": review_id}
