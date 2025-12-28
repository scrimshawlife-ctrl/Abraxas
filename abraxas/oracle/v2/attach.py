from __future__ import annotations

from typing import Any, Dict

from abraxas.oracle.v2.guard import assert_mode_lock
from abraxas.oracle.v2.wire import build_v2_block


def attach_v2_to_envelope(
    *,
    envelope: Dict[str, Any],
    checks: Dict[str, Any],
    router_input: Dict[str, Any],
    config_hash: str,
) -> Dict[str, Any]:
    """
    Economy helper:
      - Builds the v2 governance block
      - Attaches it to envelope["oracle_signal"]["v2"]
      - Enforces mode lock invariant

    Additive-only: does not mutate scores_v1.
    """
    v2 = build_v2_block(checks=checks, router_input=router_input, config_hash=config_hash)
    assert_mode_lock(v2)
    envelope.setdefault("oracle_signal", {}).setdefault("v2", {})
    envelope["oracle_signal"]["v2"] = v2
    return envelope
