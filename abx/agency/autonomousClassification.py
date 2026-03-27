from __future__ import annotations

from abx.agency.actionModes import build_action_modes


ACTION_MODE_CLASSES = {row.mode_class for row in build_action_modes()}


def classify_autonomous_operation_mode(mode: str, status: str) -> str:
    if mode not in ACTION_MODE_CLASSES:
        return "NOT_COMPUTABLE"
    if status == "BLOCKED":
        return "BLOCKED"
    if status == "DEGRADED":
        return "DEGRADED"
    return mode


def classify_autonomous_posture(mode_states: dict[str, str]) -> str:
    if not mode_states:
        return "NOT_COMPUTABLE"
    values = set(mode_states.values())
    if "BLOCKED" in values:
        return "BLOCKED"
    if "DEGRADED" in values:
        return "DEGRADED"
    if "BOUNDED_AUTONOMOUS_ACTION" in values:
        return "BOUNDED_AUTONOMOUS_ACTION"
    if "DELEGATED_ACTION" in values:
        return "DELEGATED_ACTION"
    if "OPERATOR_CONFIRMED_ACTION" in values:
        return "OPERATOR_CONFIRMED_ACTION"
    if "RECOMMENDATION_ONLY" in values:
        return "RECOMMENDATION_ONLY"
    if values == {"ANALYSIS_ONLY"}:
        return "ANALYSIS_ONLY"
    return "NOT_COMPUTABLE"
