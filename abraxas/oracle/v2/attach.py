from __future__ import annotations

from typing import Any, Dict

from abraxas.oracle.v2.wire import build_v2_block


def attach_v2_to_envelope(
    *,
    envelope: Dict[str, Any],
    checks: Dict[str, Any],
    router_input: Dict[str, Any],
    config_hash: str,
    date_iso: str | None = None,
    config_payload: Dict[str, Any] | None = None,
    config_source: str | None = None,
) -> Dict[str, Any]:
    """
    Builds the v2 governance block and attaches it to the envelope.
    Returns the modified envelope (mutates in place for economy).
    """
    v2_block = build_v2_block(
        checks=checks,
        router_input=router_input,
        config_hash=config_hash,
        date_iso=date_iso,
        config_payload=config_payload,
        config_source=config_source,
    )

    # Ensure oracle_signal exists
    if "oracle_signal" not in envelope:
        envelope["oracle_signal"] = {}

    # Attach v2 block
    envelope["oracle_signal"]["v2"] = v2_block

    return envelope
