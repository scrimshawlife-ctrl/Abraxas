from __future__ import annotations


def classify_sufficiency(*, sufficiency_state: str, consequence_class: str) -> str:
    if consequence_class in {"HIGH_CONSEQUENCE", "CRITICAL_CONSEQUENCE"} and sufficiency_state in {
        "INSUFFICIENT_MEASUREMENT",
        "MEASUREMENT_AMBIGUOUS",
    }:
        return "HIGH_CONSEQUENCE_UNDER_OBSERVED"
    return sufficiency_state
