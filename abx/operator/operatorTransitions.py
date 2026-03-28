from __future__ import annotations

from abx.operator.types import OperatorTransitionRecord


def build_operator_transition_records() -> tuple[OperatorTransitionRecord, ...]:
    return (
        OperatorTransitionRecord(
            transition_id="txn.emergency.enter.001",
            intervention_id="int.emergency.rule-hotfix.001",
            transition_kind="EMERGENCY_MODE",
            from_state="NORMAL_OPERATION",
            to_state="EMERGENCY_MANUAL_MODE_ACTIVE",
            occurred_at="2026-03-27T08:12:00Z",
        ),
        OperatorTransitionRecord(
            transition_id="txn.override.overbroad.001",
            intervention_id="int.bypass.direct-write.001",
            transition_kind="OVERRIDE_SCOPE",
            from_state="OVERRIDE_BOUNDED",
            to_state="OVERRIDE_OVERBROAD_ACTIVE",
            occurred_at="2026-03-27T03:35:00Z",
        ),
        OperatorTransitionRecord(
            transition_id="txn.restoration.missed.001",
            intervention_id="int.prohibited.policy-disable.001",
            transition_kind="RESTORATION",
            from_state="RESTORATION_REQUIRED",
            to_state="MANUAL_INTERVENTION_NOT_RESTORED",
            occurred_at="2026-03-28T01:00:00Z",
        ),
        OperatorTransitionRecord(
            transition_id="txn.emergency.expired.001",
            intervention_id="int.corrective.cache-reset.001",
            transition_kind="EMERGENCY_MODE",
            from_state="EMERGENCY_MANUAL_MODE_ACTIVE",
            to_state="EMERGENCY_MODE_EXPIRED",
            occurred_at="2026-03-28T03:00:00Z",
        ),
    )
