from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.mda.source_flow import run_source_shadow_flow
from abraxas.mda.tvm_flow import run_tvm_shadow_flow
from abraxas.oracle.attachments_registry import ATTACHMENT_BUILDERS


def _attach_aalmanac_shadow(payload: Optional[Dict[str, Any]], out: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        return

    spec = ATTACHMENT_BUILDERS.get("aalmanac_v1")
    if not spec:
        return

    extracted_terms = payload.get("extracted_terms")
    if isinstance(extracted_terms, dict):
        raw_terms = extracted_terms.get("aalmanac_terms", [])
        seed_inputs: Dict[str, Any] = {"payload": payload, "extracted_terms": extracted_terms}
    else:
        raw_terms = payload.get("aalmanac_terms", [])
        seed_inputs = payload

    if not isinstance(raw_terms, list) or not raw_terms:
        return

    attachment = spec["builder"](seed_inputs=seed_inputs, raw_terms=raw_terms, cfg=spec["config"])
    shadow = out.get("shadow") if isinstance(out.get("shadow"), dict) else {}
    shadow["aalmanac_v1"] = attachment
    out["shadow"] = shadow


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
    _attach_aalmanac_shadow(payload, out)

    return out
