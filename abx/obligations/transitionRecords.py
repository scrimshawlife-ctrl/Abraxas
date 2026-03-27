from __future__ import annotations

from abx.obligations.obligationLifecycle import build_obligation_lifecycle_records
from abx.obligations.types import ObligationTransitionRecord


FROM_STATE = {
    "IN_PROGRESS": "ACCEPTED",
    "DUE_SOON": "SCHEDULED",
    "SCHEDULED": "PROPOSED",
    "MISSED": "AT_RISK",
    "WAIVED": "AT_RISK",
}


def build_obligation_transition_records() -> list[ObligationTransitionRecord]:
    rows = [
        ObligationTransitionRecord(
            transition_id=f"transition.{row.commitment_id}",
            commitment_id=row.commitment_id,
            from_state=FROM_STATE.get(row.lifecycle_state, "UNKNOWN"),
            to_state=row.lifecycle_state,
            reason=("deadline_slip" if row.lifecycle_state == "MISSED" else "state_progression"),
        )
        for row in build_obligation_lifecycle_records()
    ]
    return sorted(rows, key=lambda x: x.transition_id)
