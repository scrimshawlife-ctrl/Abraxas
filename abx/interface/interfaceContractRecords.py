from __future__ import annotations

from abx.interface.contractInventory import build_contract_inventory
from abx.interface.types import InterfaceContractRecord


def build_interface_contract_records() -> list[InterfaceContractRecord]:
    return [
        InterfaceContractRecord(contract_id=cid, boundary_ref=bref, contract_state=state, integrity_surface=surface)
        for cid, bref, state, surface in build_contract_inventory()
    ]
