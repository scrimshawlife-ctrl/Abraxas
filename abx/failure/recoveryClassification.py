from __future__ import annotations


def classify_recovery(*, retry_allowed: str, restore_allowed: str, clearance_required: str) -> str:
    if retry_allowed == "YES" and restore_allowed == "YES":
        return "RECOVERY_ELIGIBLE"
    if clearance_required == "YES" and restore_allowed == "NO":
        return "RECOVERY_FORBIDDEN"
    if restore_allowed == "PARTIAL":
        return "PARTIAL"
    return "BLOCKED"
