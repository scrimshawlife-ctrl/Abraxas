from __future__ import annotations


def classify_horizon(*, horizon_state: str, cadence_ref: str) -> str:
    if horizon_state in {"BLOCKED", "NOT_COMPUTABLE", "HORIZON_UNKNOWN"}:
        return horizon_state
    if horizon_state in {"REAL_TIME_HORIZON", "SHORT_HORIZON", "MEDIUM_HORIZON", "LONG_HORIZON", "ARCHIVAL_HORIZON"}:
        return horizon_state
    if cadence_ref == "cadence/none":
        return "ARCHIVAL_HORIZON"
    return "MEDIUM_HORIZON"
