from __future__ import annotations

from abx.obligations.commitmentInventory import build_commitment_inventory
from abx.obligations.types import CanceledObligationRecord


def build_canceled_obligation_records() -> list[CanceledObligationRecord]:
    rows = [
        CanceledObligationRecord(
            cancellation_id=f"cancellation.{row.commitment_id}",
            commitment_id=row.commitment_id,
            cancellation_state="CANCELED",
            reason="scope_withdrawn",
        )
        for row in build_commitment_inventory()
        if row.commitment_state == "CANCELED_OBLIGATION"
    ]
    return sorted(rows, key=lambda x: x.cancellation_id)
