from __future__ import annotations

from abx.interface.acceptanceInventory import build_acceptance_inventory
from abx.interface.types import AcceptanceRecord, InterpretationRecord


def build_acceptance_records() -> list[AcceptanceRecord]:
    return [
        AcceptanceRecord(acceptance_id=aid, handoff_ref=href, acceptance_state=state, acceptance_reason=reason)
        for aid, href, state, reason in build_acceptance_inventory()
    ]


def build_interpretation_records() -> list[InterpretationRecord]:
    rows = {
        "hf.001": ("INTERPRETATION_PENDING", "payload awaiting semantic checks"),
        "hf.002": ("INTERPRETATION_STRUCTURAL_ONLY", "schema matched; semantics pending"),
        "hf.003": ("INTERPRETATION_MATCHED", "semantic map aligned"),
        "hf.004": ("INTERPRETATION_APPLIED", "receiver applied intended meaning"),
        "hf.005": ("INTERPRETATION_REJECTED", "authority check failed"),
        "hf.006": ("INTERPRETATION_COERCED", "receiver defaulted missing fields"),
        "hf.007": ("INTERPRETATION_MISMATCH", "field mapping diverged"),
        "hf.008": ("NOT_COMPUTABLE", "no interpretation evidence"),
    }
    return [
        InterpretationRecord(
            interpretation_id=f"int.{idx:03d}",
            handoff_ref=href,
            interpretation_state=state,
            interpretation_reason=reason,
        )
        for idx, (href, (state, reason)) in enumerate(rows.items(), start=1)
    ]
