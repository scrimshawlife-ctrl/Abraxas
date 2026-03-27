from __future__ import annotations


def classify_consent_state(consent_state: str) -> str:
    states = {
        "EXPLICIT_APPROVAL",
        "CONDITIONAL_APPROVAL",
        "ACKNOWLEDGMENT_ONLY",
        "PREFERENCE_ONLY",
        "AMBIGUOUS_CONSENT",
        "DENIED_CONSENT",
        "WITHDRAWN_CONSENT",
        "EXPIRED_CONSENT",
        "NOT_COMPUTABLE",
    }
    return consent_state if consent_state in states else "NOT_COMPUTABLE"
