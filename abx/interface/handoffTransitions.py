from __future__ import annotations

from abx.interface.types import DeliveryTransitionRecord


def build_delivery_transition_records() -> list[DeliveryTransitionRecord]:
    return [
        DeliveryTransitionRecord("tr.001", "hf.001", "HANDOFF_PREPARED", "HANDOFF_SENT", "sender emitted payload"),
        DeliveryTransitionRecord("tr.002", "hf.002", "HANDOFF_SENT", "HANDOFF_DELIVERED", "transport acked"),
        DeliveryTransitionRecord("tr.003", "hf.003", "HANDOFF_DELIVERED", "HANDOFF_RECEIVED", "receiver receipt persisted"),
        DeliveryTransitionRecord("tr.004", "hf.004", "HANDOFF_RECEIVED", "HANDOFF_ACCEPTED", "semantic acceptance complete"),
        DeliveryTransitionRecord("tr.005", "hf.005", "HANDOFF_RECEIVED", "DELIVERY_PARTIAL", "missing fields"),
        DeliveryTransitionRecord("tr.006", "hf.006", "HANDOFF_RECEIVED", "HANDOFF_REJECTED", "authority mismatch"),
        DeliveryTransitionRecord("tr.007", "hf.007", "HANDOFF_DELIVERED", "DELIVERY_DUPLICATED", "duplicate payload"),
        DeliveryTransitionRecord("tr.008", "hf.008", "HANDOFF_UNKNOWN", "NOT_COMPUTABLE", "no reliable telemetry"),
    ]
