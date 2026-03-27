from __future__ import annotations


def classify_commitment_state(commitment_state: str) -> str:
    if commitment_state in {
        "PROPOSED_COMMITMENT",
        "ACCEPTED_COMMITMENT",
        "CONDITIONAL_COMMITMENT",
        "SCHEDULED_OBLIGATION",
        "SUPERSEDED_OBLIGATION",
        "CANCELED_OBLIGATION",
        "BLOCKED",
        "DEGRADED",
    }:
        return commitment_state
    return "NOT_COMPUTABLE"
