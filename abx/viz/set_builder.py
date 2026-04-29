from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from abx.schemas.aal_viz_proof_state import AALVizProofState
from abx.schemas.aal_viz_proof_state_set import AALVizProofStateSet


def build_proof_state_set(items: List[AALVizProofState]) -> AALVizProofStateSet:
    ordered = sorted(items, key=lambda item: (item.get("authority_lane", ""), item.get("projection_id", "")))
    display_allowed_count = sum(1 for item in ordered if bool(item.get("display_allowed", False)))
    fail_closed_count = sum(1 for item in ordered if bool(item.get("fail_closed", False)))
    not_computable_count = sum(1 for item in ordered if str(item.get("display_status", "")) == "NOT_COMPUTABLE")
    operator_review_linked_count = sum(1 for item in ordered if bool(item.get("operator_review_item_id")))

    return {
        "schema_version": "AALVizProofStateSet.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": ordered,
        "total_items": len(ordered),
        "display_allowed_count": display_allowed_count,
        "fail_closed_count": fail_closed_count,
        "not_computable_count": not_computable_count,
        "operator_review_linked_count": operator_review_linked_count,
    }
