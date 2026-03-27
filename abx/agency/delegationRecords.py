from __future__ import annotations

from abx.agency.delegationClassification import classify_delegation_state
from abx.agency.delegationInventory import build_delegation_inventory
from abx.agency.types import DelegationChainRecord


def build_delegation_chains() -> list[DelegationChainRecord]:
    rows = []
    for record in build_delegation_inventory():
        hops = [record.origin_actor, record.delegate_actor]
        depth = len(hops) - 1
        recursion_state = classify_delegation_state(handoff_type=record.handoff_type, depth=depth, max_depth=record.max_depth)
        rows.append(
            DelegationChainRecord(
                chain_id=f"chain.{record.delegation_id}",
                origin_authority=record.origin_actor,
                hops=hops,
                depth=depth,
                recursion_state=recursion_state,
            )
        )
    return sorted(rows, key=lambda x: x.chain_id)
