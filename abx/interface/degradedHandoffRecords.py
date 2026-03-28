from __future__ import annotations

from abx.interface.types import DegradedHandoffRecord


def build_degraded_handoff_records() -> list[DegradedHandoffRecord]:
    return [
        DegradedHandoffRecord("dg.001", "hf.005", "DELIVERY_PARTIAL", "only required subset transferred"),
        DegradedHandoffRecord("dg.002", "hf.006", "DELIVERY_STALE", "payload timestamp outside freshness window"),
        DegradedHandoffRecord("dg.003", "hf.007", "DELIVERY_DUPLICATED", "idempotency key reused"),
        DegradedHandoffRecord("dg.004", "hf.008", "REDELIVERY_REQUIRED", "delivery trace incomplete"),
        DegradedHandoffRecord("dg.005", "hf.005", "TRUST_DOWNGRADED", "boundary integrity degraded"),
    ]
