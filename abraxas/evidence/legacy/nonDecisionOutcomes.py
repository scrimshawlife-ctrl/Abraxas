from __future__ import annotations


def classify_non_decision(readiness_state: str) -> str:
    if readiness_state in {"DEFERRED_PENDING_EVIDENCE", "ABSTAINED", "ESCALATED", "BLOCKED"}:
        return readiness_state
    return "NONE"
