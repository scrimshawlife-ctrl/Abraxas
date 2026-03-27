from __future__ import annotations


def classify_obligation_lifecycle_state(lifecycle_state: str, discharge_state: str) -> str:
    if lifecycle_state in {"ACCEPTED", "SCHEDULED", "IN_PROGRESS", "DUE_SOON", "AT_RISK", "BLOCKED", "MISSED", "WAIVED"}:
        if discharge_state == "DISCHARGED":
            return "DISCHARGED"
        if discharge_state == "PARTIALLY_DISCHARGED":
            return "PARTIALLY_DISCHARGED"
        return lifecycle_state
    if discharge_state in {"DISCHARGED", "PARTIALLY_DISCHARGED", "MISSED", "WAIVED"}:
        return discharge_state
    return "NOT_COMPUTABLE"
