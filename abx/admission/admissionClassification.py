from __future__ import annotations


def classify_admission(*, admission_state: str, evidence_state: str) -> str:
    if admission_state == "NOT_COMPUTABLE" or evidence_state == "EVIDENCE_NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if admission_state in {"ADMISSION_REJECTED", "ADMISSION_BLOCKED"}:
        return admission_state
    return admission_state
