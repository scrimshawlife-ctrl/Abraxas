from __future__ import annotations


def classify_effect_realization(*, realization_state: str, evidence_mode: str) -> str:
    if realization_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if realization_state == "EFFECT_UNVERIFIED" and evidence_mode == "ASSUMED":
        return "VERIFICATION_REQUIRED"
    return realization_state
