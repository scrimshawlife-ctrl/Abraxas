from typing import Literal, Optional, TypedDict


class AALVizProofState(TypedDict):
    schema_version: Literal["AALVizProofState.v1"]
    projection_id: str
    source_artifact_path: str
    source_artifact_sha256: str
    authority_lane: Literal["FORECAST", "PROJECTION", "SHADOW"]
    display_status: Literal["OK", "BLOCKED", "NOT_COMPUTABLE"]
    fail_closed: Literal[True]
    display_allowed: bool
    operator_review_item_id: Optional[str]
    ui_inferred_authority_allowed: Literal[False]
