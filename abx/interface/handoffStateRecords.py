from __future__ import annotations

from abx.interface.handoffInventory import build_handoff_inventory
from abx.interface.types import DeliveryRecord, HandoffStateRecord


def build_handoff_state_records() -> list[HandoffStateRecord]:
    return [
        HandoffStateRecord(handoff_id=hid, boundary_ref=bref, handoff_state=state, transport_state=tstate)
        for hid, bref, state, tstate in build_handoff_inventory()
    ]


def build_delivery_records() -> list[DeliveryRecord]:
    rows = {
        "hf.001": ("DELIVERY_PENDING", "prepared but not sent"),
        "hf.002": ("DELIVERY_IN_PROGRESS", "transport inflight"),
        "hf.003": ("DELIVERY_COMPLETE", "delivery acknowledged"),
        "hf.004": ("DELIVERY_COMPLETE", "receiver confirms receipt"),
        "hf.005": ("DELIVERY_PENDING", "retry window active"),
        "hf.006": ("DELIVERY_FAILED", "receiver rejected transfer"),
        "hf.007": ("DELIVERY_UNKNOWN", "state telemetry missing"),
        "hf.008": ("NOT_COMPUTABLE", "missing transport evidence"),
    }
    return [
        DeliveryRecord(delivery_id=f"del.{idx:03d}", handoff_ref=hid, delivery_state=state, delivery_reason=reason)
        for idx, (hid, (state, reason)) in enumerate(rows.items(), start=1)
    ]
