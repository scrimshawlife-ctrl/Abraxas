from __future__ import annotations

from abx.capacity.commitmentInventory import build_allocation_inventory, build_commitment_inventory
from abx.capacity.types import AllocationRecord, CapacityCommitmentRecord


def build_capacity_commitment_records() -> list[CapacityCommitmentRecord]:
    return [
        CapacityCommitmentRecord(commitment_id=cid, resource_ref=resource_ref, commitment_state=state, commitment_reason=reason)
        for cid, resource_ref, state, reason in build_commitment_inventory()
    ]


def build_allocation_records() -> list[AllocationRecord]:
    return [
        AllocationRecord(allocation_id=aid, resource_ref=resource_ref, allocation_state=state, allocation_reason=reason)
        for aid, resource_ref, state, reason in build_allocation_inventory()
    ]
