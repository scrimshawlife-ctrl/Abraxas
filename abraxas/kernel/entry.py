# =========================
# FILE: abraxas/kernel/entry.py
# PURPOSE: Route ASCEND to the whitelist executor
# =========================

from __future__ import annotations
from typing import Any, Dict, Literal

Phase = Literal["OPEN", "ALIGN", "ASCEND", "CLEAR", "SEAL"]

def run_phase(phase: Phase, payload: Dict[str, Any]) -> Dict[str, Any]:
    if phase == "OPEN":
        prompt = str(payload.get("prompt", ""))
        return {"mode": "OPEN", "signal": "intake_ok", "prompt_len": len(prompt)}

    if phase == "ALIGN":
        op = str(payload.get("op", payload.get("intent", "unspecified")))
        return {
            "mode": "ALIGN",
            "op": op,
            "constraints": {"determinism": True, "provenance": True}
        }

    if phase == "CLEAR":
        text = str(payload.get("text", payload.get("prompt", "")))
        compact = " ".join(text.split())
        return {
            "mode": "CLEAR",
            "text_compact": compact[:1024],
            "chars_in": len(text),
            "chars_out": len(compact),
        }

    if phase == "SEAL":
        title = str(payload.get("title", "Abraxas Artifact"))
        return {"mode": "SEAL", "artifact": {"title": title, "status": "sealed_stub"}}

    if phase == "ASCEND":
        # ASCEND is now a scoped executor — no IO, no writes, whitelist only.
        from abraxas.kernel.ascend_ops import execute_ascend
        return execute_ascend(payload)

    raise ValueError(f"Unsupported phase: {phase}")
