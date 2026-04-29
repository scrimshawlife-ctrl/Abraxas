from typing import List, Literal, TypedDict

from .aal_viz_proof_state import AALVizProofState


class AALVizProofStateSet(TypedDict):
    schema_version: Literal["AALVizProofStateSet.v1"]
    generated_at: str
    items: List[AALVizProofState]
    total_items: int
    display_allowed_count: int
    fail_closed_count: int
    not_computable_count: int
    operator_review_linked_count: int
