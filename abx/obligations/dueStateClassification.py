from __future__ import annotations


def classify_due_state(*, deadline_kind: str, commitment_state: str, due_date: str) -> tuple[str, str]:
    if commitment_state in {"CANCELED_OBLIGATION", "SUPERSEDED_OBLIGATION"}:
        return ("SUPERSEDED", "LOW")
    if deadline_kind == "HARD_DEADLINE":
        return ("DUE_SOON", "AT_RISK")
    if deadline_kind == "DUE_WINDOW":
        return ("AT_RISK", "AT_RISK")
    if deadline_kind == "SOFT_TARGET":
        return ("SCHEDULED", "LOW")
    return ("NOT_COMPUTABLE", "NOT_COMPUTABLE")
