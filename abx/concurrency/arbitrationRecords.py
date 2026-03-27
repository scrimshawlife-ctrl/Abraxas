from __future__ import annotations

from abx.concurrency.arbitrationClassification import classify_arbitration_outcome
from abx.concurrency.conflictInventory import build_conflict_inventory
from abx.concurrency.types import ArbitrationDecisionRecord


def build_arbitration_decisions() -> list[ArbitrationDecisionRecord]:
    rows: list[ArbitrationDecisionRecord] = []
    for row in build_conflict_inventory():
        outcome = classify_arbitration_outcome(row.conflict_class)
        winner = row.left_operation_id
        loser = row.right_operation_id
        if outcome in {"DENIED", "BLOCKED", "NOT_COMPUTABLE"}:
            winner = "none"
            loser = "both"
        rationale = f"{row.conflict_class}:{outcome}"
        rows.append(
            ArbitrationDecisionRecord(
                decision_id=f"decision.{row.conflict_id}",
                conflict_id=row.conflict_id,
                outcome=outcome,
                winner_operation_id=winner,
                loser_operation_id=loser,
                rationale=rationale,
            )
        )
    return sorted(rows, key=lambda x: x.decision_id)
