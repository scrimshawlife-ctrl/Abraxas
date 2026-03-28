from __future__ import annotations

from abx.capacity.resourceInventory import build_resource_inventory
from abx.capacity.types import ResourceReservationRecord


def build_resource_reservation_records() -> list[ResourceReservationRecord]:
    return [
        ResourceReservationRecord(
            reservation_id=rid,
            resource_ref=resource_ref,
            reservation_state=reservation_state,
            actor_ref=actor_ref,
        )
        for rid, resource_ref, reservation_state, actor_ref in build_resource_inventory()
    ]
