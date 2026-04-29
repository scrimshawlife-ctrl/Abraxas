from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from abx.schemas.operator_queue import OperatorQueue
from abx.schemas.operator_review_item import OperatorReviewItem


_PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}


def build_operator_queue(items: List[OperatorReviewItem]) -> OperatorQueue:
    ordered = sorted(
        items,
        key=lambda item: (
            _PRIORITY_ORDER.get(str(item.get("priority", "P2")), 2),
            str(item.get("source_system", "")),
            str(item.get("review_id", "")),
        ),
    )
    p0_count = sum(1 for item in ordered if item.get("priority") == "P0")
    p1_count = sum(1 for item in ordered if item.get("priority") == "P1")
    p2_count = sum(1 for item in ordered if item.get("priority") == "P2")

    return {
        "schema_version": "OperatorQueue.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": ordered,
        "total_items": len(ordered),
        "p0_count": p0_count,
        "p1_count": p1_count,
        "p2_count": p2_count,
        "operator_action_required": bool(p0_count or p1_count),
    }
