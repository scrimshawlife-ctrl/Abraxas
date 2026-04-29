from typing import Dict, List, Literal, TypedDict


class DomainWeightAdvisory(TypedDict):
    schema_version: Literal["DomainWeightAdvisory.v1"]
    generated_at: str
    input_ref: str
    base_weights: Dict[str, float]
    adjusted_weights: Dict[str, float]
    adjustment_reason: Literal[
        "CALIBRATION_PASS",
        "CALIBRATION_REVIEW_REQUIRED",
        "CALIBRATION_FAIL",
        "NOT_COMPUTABLE",
    ]
    confidence: float
    dominant_domain: str
    drift_detected: bool
    evidence_refs: List[str]
    advisory_only: Literal[True]
