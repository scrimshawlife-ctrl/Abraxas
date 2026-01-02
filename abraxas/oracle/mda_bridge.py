from __future__ import annotations

from typing import Any, Dict, Optional


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
    out: Dict[str, Any] = {
        "envelope": {
            "env": env,
            "run_at": run_at,
        },
        "domain_aggregates": {},
        "dsp": [],
        "fusion_graph": {},
    }
    if isinstance(payload, dict) and isinstance(payload.get("shadow"), dict):
        out["shadow"] = payload.get("shadow")
    return out
