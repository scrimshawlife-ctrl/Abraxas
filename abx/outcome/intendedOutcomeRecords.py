from __future__ import annotations

from abx.outcome.intendedOutcomeInventory import build_intended_outcome_inventory
from abx.outcome.types import IntendedOutcomeRecord


def build_intended_outcome_records() -> list[IntendedOutcomeRecord]:
    return [
        IntendedOutcomeRecord(outcome_id=oid, action_ref=action_ref, intended_state=state, effect_surface=surface)
        for oid, action_ref, state, surface in build_intended_outcome_inventory()
    ]
