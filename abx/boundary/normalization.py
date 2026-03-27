from __future__ import annotations

from abx.boundary.types import InputEnvelope, NormalizedInput, ProvenanceCarryRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def normalize_envelope(envelope: InputEnvelope) -> tuple[NormalizedInput, ProvenanceCarryRecord]:
    payload = dict(envelope.payload)
    normalized_payload = {k: payload[k] for k in sorted(payload)}
    for key in ("run_id", "scenario_id"):
        if key in normalized_payload and isinstance(normalized_payload[key], str):
            normalized_payload[key] = normalized_payload[key].strip().upper()

    steps = ["sort-keys", "normalize-run-scenario-case"]
    digest = sha256_bytes(
        dumps_stable({"envelope_id": envelope.envelope_id, "normalized_payload": normalized_payload, "steps": steps}).encode("utf-8")
    )
    normalized = NormalizedInput(
        normalized_id=f"norm-{digest[:16]}",
        envelope_id=envelope.envelope_id,
        normalized_payload=normalized_payload,
        normalization_steps=steps,
    )
    provenance = ProvenanceCarryRecord(
        envelope_id=envelope.envelope_id,
        source=envelope.source,
        trust_state=envelope.trust_state,
        carried_fields=["source", "trust_state", "interface_id", "received_tick"],
    )
    return normalized, provenance
