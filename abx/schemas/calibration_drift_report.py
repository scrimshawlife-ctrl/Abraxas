from typing import List, Literal, TypedDict


class CalibrationDriftReport(TypedDict):
    schema_version: Literal["CalibrationDriftReport.v1"]
    generated_at: str
    mean_brier: float
    sample_size: int
    not_computable_count: int
    calibration_drift_status: Literal["PASS", "REVIEW_REQUIRED", "FAIL", "NOT_COMPUTABLE"]
    promotion_gate_status: Literal["PASS", "BLOCKED", "FAIL", "NOT_COMPUTABLE"]
    dominant_failure_mode: str
    evidence_refs: List[str]
