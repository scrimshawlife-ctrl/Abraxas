from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.mda.source_flow import run_source_shadow_flow
from abraxas.mda.tvm_flow import run_tvm_shadow_flow


def run_mda_for_oracle(
    payload: Optional[Dict[str, Any]],
    *,
    env: str,
    run_at: str,
) -> Dict[str, Any]:
    """
    Minimal MDA bridge for batch packaging.

    This produces an MDA-like output shell with optional shadow attachment
    from the payload (if present). It is deterministic for stable inputs.
    """
    envelope = {
        "env": env,
        "run_at": run_at,
    }
    out: Dict[str, Any] = {
        "envelope": envelope,
        "domain_aggregates": {},
        "dsp": [],
        "fusion_graph": {},
    }
    if isinstance(payload, dict) and isinstance(payload.get("shadow"), dict):
        out["shadow"] = payload.get("shadow")

    observations = None
    if isinstance(payload, dict):
        observations = payload.get("observations")
    source_flow = run_source_shadow_flow(env=envelope, subsystem_id="mda_bridge")
    shadow_flow = run_tvm_shadow_flow(observations=observations, env=envelope, subsystem_id="mda_bridge")
    out["shadow"] = {**(out.get("shadow") or {}), **source_flow["shadow"], **shadow_flow["shadow"]}
    out["tvm_frames"] = shadow_flow["tvm_frames"]
    out["envelope"]["mda_run_id"] = shadow_flow["run_id"]
    out["envelope"]["source_run_id"] = source_flow["run_id"]

    return out
