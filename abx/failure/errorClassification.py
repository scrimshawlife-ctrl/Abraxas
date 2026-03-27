from __future__ import annotations


def classify_error(*, failure_class: str, severity: str) -> str:
    if failure_class not in {
        "TRANSIENT_ERROR",
        "PERSISTENT_ERROR",
        "EXTERNAL_DEPENDENCY_FAILURE",
        "INTERNAL_LOGIC_FAILURE",
        "STATE_INVALIDITY",
        "INTEGRITY_RISK_FAILURE",
        "SAFETY_BLOCKING_FAILURE",
        "UNKNOWN_FAILURE",
    }:
        return "NOT_COMPUTABLE"
    if severity == "CRITICAL":
        return "BLOCKED"
    return failure_class
