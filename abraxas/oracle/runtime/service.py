from __future__ import annotations

from typing import Any, Mapping, Sequence

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.oracle.advisory.registry import default_registry
from abraxas.oracle.runtime.authority_builder import build_authority_output_v2
from abraxas.oracle.runtime.compression_ops import compress_signal_v0, dedupe_signal_items_v0
from abraxas.oracle.runtime.input_normalizer import normalize_input_v2
from abraxas.oracle.runtime.output_envelope import build_output_envelope_v2
from abraxas.oracle.runtime.schema_guard import validate_oslv2_input, validate_oslv2_output


def run_oracle_signal_layer_v2_service(raw_envelope: Mapping[str, Any], *, advisory_ids: Sequence[str] | None = None) -> dict:
    validate_oslv2_input(raw_envelope)
    normalized = normalize_input_v2(raw_envelope)
    metadata = dict(normalized["hashable_core"]["metadata"])
    lane = str(metadata.get("lane", "shadow"))
    run_id = str(dict(raw_envelope.get("metadata") or {}).get("run_id", "oracle_signal_v2_run"))

    observations = list(dict(normalized["hashable_core"]["payload"]).get("observations") or [])
    compressed = compress_signal_v0(observations)
    deduped = dedupe_signal_items_v0(compressed)
    authority = build_authority_output_v2(
        run_id=run_id,
        lane=lane,
        normalized_core_hash=str(normalized["core_hash"]),
        compressed_items=deduped,
    )

    authority_hash_before = sha256_hex(canonical_json(authority))

    registry = default_registry()
    attachments = registry.invoke(
        authority=authority,
        normalized=normalized,
        requested_ids=advisory_ids,
    )

    authority_hash_after = sha256_hex(canonical_json(authority))
    if authority_hash_before != authority_hash_after:
        raise ValueError("authority payload changed during advisory attachment")

    output = build_output_envelope_v2(
        run_id=run_id,
        lane=lane,
        authority=authority,
        advisory_attachments=attachments,
        input_hash=str(normalized["core_hash"]),
        not_computable_reasons=normalized["not_computable_reasons"],
    )
    output["not_computable_reasons"] = list(normalized["not_computable_reasons"])
    output["display_fields"] = dict(normalized["display_fields"])
    validate_oslv2_output(output)
    return output
