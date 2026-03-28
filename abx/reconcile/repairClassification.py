from __future__ import annotations


def classify_repair(*, repair_mode: str, reconciliation_state: str, legitimacy_state: str) -> str:
    if reconciliation_state == "NOT_COMPUTABLE" or legitimacy_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if repair_mode == "REPAIR_FORBIDDEN" or legitimacy_state == "FORBIDDEN":
        return "REPAIR_FORBIDDEN"
    if legitimacy_state == "UNKNOWN" or repair_mode == "REPAIR_LEGITIMACY_UNKNOWN":
        return "REPAIR_LEGITIMACY_UNKNOWN"
    return repair_mode
