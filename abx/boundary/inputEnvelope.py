from __future__ import annotations

from typing import Any

from abx.boundary.trustModel import classify_trust_from_source
from abx.boundary.types import InputEnvelope
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_input_envelope(*, source: str, interface_id: str, payload: dict[str, Any], received_tick: int = 0) -> InputEnvelope:
    trust_state, _ = classify_trust_from_source(source)
    digest = sha256_bytes(
        dumps_stable(
            {
                "source": source,
                "interface_id": interface_id,
                "payload": payload,
                "received_tick": int(received_tick),
                "trust_state": trust_state,
            }
        ).encode("utf-8")
    )
    return InputEnvelope(
        envelope_id=f"env-{digest[:16]}",
        source=source,
        interface_id=interface_id,
        payload=payload,
        trust_state=trust_state,
        received_tick=int(received_tick),
    )
