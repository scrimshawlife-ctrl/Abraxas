from typing import List, Literal, TypedDict


class OperatorReviewItem(TypedDict):
    schema_version: Literal["OperatorReviewItem.v1"]
    review_id: str
    created_at: str
    source_system: Literal["calibration", "weighting", "fusion", "adversarial"]
    decision_type: Literal["REVIEW", "REQUEST_EVIDENCE", "NO_ACTION"]
    priority: Literal["P0", "P1", "P2"]
    reason: str
    evidence_refs: List[str]
    operator_required: Literal[True]
    auto_apply_allowed: Literal[False]
