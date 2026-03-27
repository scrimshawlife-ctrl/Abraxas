from __future__ import annotations

from abx.agency.types import ActionModeRecord


def build_action_modes() -> list[ActionModeRecord]:
    rows = [
        ActionModeRecord("mode.analysis_only", "ANALYSIS_ONLY", "NO_SIDE_EFFECTS", False),
        ActionModeRecord("mode.recommendation_only", "RECOMMENDATION_ONLY", "NO_SIDE_EFFECTS", False),
        ActionModeRecord("mode.operator_confirmed", "OPERATOR_CONFIRMED_ACTION", "SIDE_EFFECT_CAPABLE", True),
        ActionModeRecord("mode.delegated", "DELEGATED_ACTION", "SIDE_EFFECT_CAPABLE", True),
        ActionModeRecord("mode.bounded_autonomous", "BOUNDED_AUTONOMOUS_ACTION", "SIDE_EFFECT_CAPABLE", True),
        ActionModeRecord("mode.blocked", "BLOCKED", "SIDE_EFFECT_BLOCKED", False),
        ActionModeRecord("mode.not_computable", "NOT_COMPUTABLE", "UNKNOWN", False),
    ]
    return sorted(rows, key=lambda x: x.mode_id)
