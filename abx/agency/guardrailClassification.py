from __future__ import annotations


def classify_guardrail_state(*, enforcement_state: str, trigger_state: str) -> str:
    if trigger_state == "TRIPPED":
        return "TRIPPED"
    if enforcement_state == "HALTED":
        return "HALTED"
    if enforcement_state == "PERMITTED_WITH_CONFIRMATION":
        return "PERMITTED_WITH_CONFIRMATION"
    if enforcement_state == "PERMITTED_WITH_BUDGET":
        return "PERMITTED_WITH_BUDGET"
    if enforcement_state == "BLOCKED":
        return "BLOCKED"
    return "NOT_COMPUTABLE"


def classify_guardrail_posture(states: dict[str, str]) -> str:
    if not states:
        return "NOT_COMPUTABLE"
    values = set(states.values())
    if "TRIPPED" in values or "HALTED" in values:
        return "DEGRADED"
    if values <= {"PERMITTED_WITH_CONFIRMATION", "PERMITTED_WITH_BUDGET"}:
        return "GUARDRAILED"
    if "BLOCKED" in values:
        return "BLOCKED"
    return "PARTIAL"
