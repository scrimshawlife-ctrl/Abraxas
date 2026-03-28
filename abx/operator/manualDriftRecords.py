from __future__ import annotations

from abx.operator.types import ManualDriftRecord


def build_manual_drift_records() -> tuple[ManualDriftRecord, ...]:
    return (
        ManualDriftRecord(
            drift_id="drift.identity.direct-write.001",
            intervention_id="int.bypass.direct-write.001",
            drift_state="MANUAL_DRIFT_SUSPECTED",
            evidence_ref="effect.direct-write.001",
        ),
        ManualDriftRecord(
            drift_id="drift.policy-disable.001",
            intervention_id="int.prohibited.policy-disable.001",
            drift_state="TRUST_DOWNGRADED",
            evidence_ref="effect.policy-disabled.001",
        ),
    )
