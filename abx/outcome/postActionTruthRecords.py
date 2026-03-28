from __future__ import annotations

from abx.outcome.postActionTruthInventory import build_contradictory_outcome_inventory, build_post_action_truth_inventory
from abx.outcome.types import ContradictoryOutcomeRecord, PostActionTruthRecord


def build_post_action_truth_records() -> list[PostActionTruthRecord]:
    return [
        PostActionTruthRecord(truth_id=tid, action_ref=action_ref, truth_state=state, truth_reason=reason)
        for tid, action_ref, state, reason in build_post_action_truth_inventory()
    ]


def build_contradictory_outcome_records() -> list[ContradictoryOutcomeRecord]:
    return [
        ContradictoryOutcomeRecord(contradiction_id=cid, action_ref=action_ref, contradiction_state=state, contradiction_reason=reason)
        for cid, action_ref, state, reason in build_contradictory_outcome_inventory()
    ]
