from __future__ import annotations


def classify_threshold_state(*, threshold_value: float, evidence_strength: float, consequence_level: str) -> str:
    if evidence_strength < 0:
        return "NOT_COMPUTABLE"
    if consequence_level == "HIGH" and evidence_strength < 0.6:
        return "ESCALATION_REQUIRED"
    if evidence_strength >= threshold_value:
        return "THRESHOLD_MET"
    if evidence_strength >= max(0.0, threshold_value - 0.1):
        return "THRESHOLD_PROVISIONALLY_MET"
    return "THRESHOLD_UNMET"
