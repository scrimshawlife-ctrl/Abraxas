from __future__ import annotations


def classify_release_readiness(*, readiness_state: str) -> str:
    if readiness_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    return readiness_state
