from __future__ import annotations

from typing import Any, Mapping

from abraxas.contracts.oracle_signal_input_envelope_v2 import OracleSignalInputEnvelopeV2
from abraxas.core.canonical import canonical_json, sha256_hex


def normalize_input_v2(raw: Mapping[str, Any]) -> dict[str, Any]:
    env = OracleSignalInputEnvelopeV2.from_dict(raw)
    metadata = dict(env.metadata)
    lane = str(metadata.get("lane", "shadow"))
    tier = str(metadata.get("tier", "advisory"))
    provenance = dict(metadata.get("provenance") or {})
    hashable_core = {
        "signal_sources": list(env.signal_sources),
        "payload": dict(env.payload),
        "context": dict(env.context),
        "metadata": {
            "lane": lane,
            "tier": tier,
            "provenance": provenance,
        },
    }
    display_fields = {
        "display_label": metadata.get("display_label"),
        "operator_note": metadata.get("operator_note"),
    }
    not_computable_reasons = []
    if not env.payload.get("observations"):
        not_computable_reasons.append("missing_observations")
    return {
        "schema_id": env.schema_id,
        "signal_sources": list(env.signal_sources),
        "hashable_core": hashable_core,
        "display_fields": display_fields,
        "not_computable_reasons": not_computable_reasons,
        "core_hash": sha256_hex(canonical_json(hashable_core)),
    }
