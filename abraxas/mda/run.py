from __future__ import annotations

from typing import Any, Dict, Tuple

from abraxas.mda.source_flow import run_source_shadow_flow
from abraxas.mda.tvm_flow import run_tvm_shadow_flow


def run_mda(
    env: Dict[str, Any],
    *,
    abraxas_version: str | None = None,
    registry: Any | None = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Minimal deterministic MDA runner for sandbox usage.

    This is a placeholder pipeline wrapper that preserves inputs and
    returns an empty analysis shell suitable for shadow attachments.
    """
    envelope = {
        "env": env,
        "abraxas_version": abraxas_version or "unknown",
    }
    out = {
        "envelope": envelope,
        "domain_aggregates": {},
        "dsp": [],
        "fusion_graph": {},
    }

    observations = env.get("observations") if isinstance(env, dict) else None
    source_flow = run_source_shadow_flow(env=envelope)
    shadow_flow = run_tvm_shadow_flow(observations=observations, env=envelope)
    out["shadow"] = {**source_flow["shadow"], **shadow_flow["shadow"]}
    out["tvm_frames"] = shadow_flow["tvm_frames"]
    out["envelope"]["mda_run_id"] = shadow_flow["run_id"]
    out["envelope"]["source_run_id"] = source_flow["run_id"]

    return env, out
