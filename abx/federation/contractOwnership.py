from __future__ import annotations

from abx.federation.crossSystemContracts import build_cross_system_contracts


def contract_ownership_report() -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for row in build_cross_system_contracts():
        owners.setdefault(row.owner, []).append(row.contract_id)
    return {k: sorted(v) for k, v in sorted(owners.items())}
