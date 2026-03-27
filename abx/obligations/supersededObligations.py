from __future__ import annotations

from abx.obligations.commitmentInventory import build_commitment_inventory
from abx.obligations.types import SupersededObligationRecord


def build_superseded_obligation_records() -> list[SupersededObligationRecord]:
    rows = [
        SupersededObligationRecord(
            supersession_id=f"supersede.{row.commitment_id}",
            commitment_id=row.commitment_id,
            superseded_by="commitment.release-v1-6",
            reason="replacement_window_agreed",
        )
        for row in build_commitment_inventory()
        if row.commitment_state == "SUPERSEDED_OBLIGATION"
    ]
    return sorted(rows, key=lambda x: x.supersession_id)
