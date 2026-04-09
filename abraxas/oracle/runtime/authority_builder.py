from __future__ import annotations

from typing import Mapping, Sequence

from abraxas.contracts.oracle_signal_authority_output_v2 import OracleSignalAuthorityOutputV2
from abraxas.contracts.oracle_signal_item_v2 import OracleSignalItemV2
from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.oracle.runtime.router import route_signal_item_v0


def build_authority_output_v2(
    *,
    run_id: str,
    lane: str,
    normalized_core_hash: str,
    compressed_items: Sequence[Mapping[str, object]],
) -> dict:
    materialized: list[dict] = []
    for raw in compressed_items:
        routing = route_signal_item_v0(raw)
        signal_id = sha256_hex(f"{raw['domain']}:{raw['subdomain']}:{raw['score']}:{raw['confidence']}")[:16]
        item = OracleSignalItemV2(
            signal_id=signal_id,
            domain=str(raw["domain"]),
            subdomain=str(raw["subdomain"]),
            score=float(raw["score"]),
            confidence=float(raw["confidence"]),
            decay=float(raw["decay"]),
            tier=routing["tier"],
            route=routing["route"],
        )
        materialized.append(item.to_dict())
    authority_hash = sha256_hex(canonical_json(materialized))
    computable = len(materialized) > 0
    authority = OracleSignalAuthorityOutputV2(
        run_id=run_id,
        lane=lane,
        items=materialized,
        authority_scope="interpretation_only",
        provenance={
            "core_hash": normalized_core_hash,
            "authority_hash": authority_hash,
            "computable": computable,
            "status": "COMPUTABLE" if computable else "NOT_COMPUTABLE",
        },
    )
    return authority.to_dict()
