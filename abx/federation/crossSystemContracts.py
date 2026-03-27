from __future__ import annotations

from abx.federation.types import CrossSystemContractRecord


def build_cross_system_contracts() -> list[CrossSystemContractRecord]:
    rows = [
        CrossSystemContractRecord("contract.input.envelope.v1", "boundary", "authoritative", "full"),
        CrossSystemContractRecord("contract.runtime.events.v1", "runtime", "authoritative", "full"),
        CrossSystemContractRecord("contract.recovery.status.v1", "resilience", "adapted", "partial"),
        CrossSystemContractRecord("contract.continuity.snapshot.v1", "knowledge", "authoritative", "full"),
    ]
    return sorted(rows, key=lambda x: x.contract_id)
