from __future__ import annotations

import json
import os
from typing import Any, Dict


def _bucket(value: float) -> str:
    if value >= 0.70:
        return "HIGH"
    if value >= 0.40:
        return "MED"
    return "LOW"


def load_dmx_context(mwr_path: str) -> Dict[str, Any]:
    """
    Load DMX context from an MWR artifact. Deterministic fallback if missing.
    Returns a small context dict to stamp into prediction rows.
    """
    ctx: Dict[str, Any] = {
        "version": "dmx.v0.1",
        "overall_manipulation_risk": 0.0,
        "bucket": "LOW",
    }
    if not mwr_path or not os.path.exists(mwr_path):
        return ctx
    try:
        with open(mwr_path, "r", encoding="utf-8") as f:
            mwr = json.load(f)
        if not isinstance(mwr, dict):
            return ctx
        dmx = mwr.get("dmx") or {}
        if not isinstance(dmx, dict):
            return ctx
        overall = float(dmx.get("overall_manipulation_risk") or 0.0)
        ctx["overall_manipulation_risk"] = overall
        ctx["bucket"] = _bucket(overall)
        if dmx.get("version"):
            ctx["version"] = str(dmx.get("version"))
        return ctx
    except Exception:
        return ctx
