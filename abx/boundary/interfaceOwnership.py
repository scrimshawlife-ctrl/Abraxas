from __future__ import annotations

from abx.boundary.interfaceContracts import build_interface_contracts


def interface_ownership_report() -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for contract in build_interface_contracts():
        owners.setdefault(contract.owner, []).append(contract.interface_id)
    return {owner: sorted(items) for owner, items in sorted(owners.items())}
