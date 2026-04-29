from typing import Dict, List, Literal, TypedDict


class CrossDomainFusionProjection(TypedDict):
    schema_version: Literal["CrossDomainFusionProjection.v1"]
    generated_at: str
    calibration_ref: str
    advisory_ref: str
    fused_priority_score: float
    domain_pressure_vector: Dict[str, float]
    dominant_domain: str
    dominance_ratio: float
    drift_alerts: List[str]
    authority_effect: Literal["ADVISORY_ONLY"]
    confidence: float
    evidence_refs: List[str]
