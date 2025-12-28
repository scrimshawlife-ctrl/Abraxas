from __future__ import annotations

from typing import Any, Dict

from abraxas.oracle.v2.attach import attach_v2_to_envelope
from abraxas.oracle.v2.collect import collect_v2_checks, derive_router_input_from_envelope
from abraxas.oracle.v2.stabilization import stabilization_tick


def attach_v2(
    *,
    envelope: Dict[str, Any],
    config_hash: str,
    thresholds: Dict[str, float] | None = None,
    user_mode_request: str | None = None,
    do_stabilization_tick: bool = True,
    ledger_path: str | None = None,
    date_iso: str | None = None,
    # checks override (optional) — can be wired later to real telemetry:
    checks: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    One-call integration point:
      1) derives router inputs from current envelope (v1 + any v2 info)
      2) builds v2 governance block (compliance + mode_decision lock)
      3) attaches into envelope
      4) optionally appends stabilization row (JSONL)
    """
    ch = checks or collect_v2_checks()
    router_input = derive_router_input_from_envelope(
        envelope=envelope, thresholds=thresholds, user_mode_request=user_mode_request
    )
    out = attach_v2_to_envelope(
        envelope=envelope, checks=ch, router_input=router_input, config_hash=config_hash
    )
    if do_stabilization_tick:
        stabilization_tick(
            v2_block=out["oracle_signal"]["v2"], ledger_path=ledger_path, date_iso=date_iso
        )
    return out
