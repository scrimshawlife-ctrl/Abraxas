from typing import List, Literal, TypedDict

from .operator_review_item import OperatorReviewItem


class OperatorQueue(TypedDict):
    schema_version: Literal["OperatorQueue.v1"]
    generated_at: str
    items: List[OperatorReviewItem]
    total_items: int
    p0_count: int
    p1_count: int
    p2_count: int
    operator_action_required: bool
