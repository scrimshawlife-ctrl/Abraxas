from __future__ import annotations


def classify_contract(*, contract_state: str, integrity_surface: str) -> str:
    if contract_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if contract_state == "CONTRACT_BROKEN":
        return "CONTRACT_BROKEN"
    if contract_state == "CONTRACT_DRIFT_SUSPECTED":
        return "CONTRACT_DRIFT_SUSPECTED"
    return integrity_surface
