# =========================
# FILE: abraxas/kernel/ascend_ops.py
# =========================
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Callable, List
import json
import hashlib

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class OpSpec:
    fn: Callable[[Dict[str, Any]], Dict[str, Any]]
    required_caps: List[str]  # informational; AAL-Core enforces via manifest op_policy

def op_hash(payload: Dict[str, Any]) -> Dict[str, Any]:
    value = payload.get("value", "")
    s = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    return {"op": "hash", "sha256": _sha256(s)}

def op_echo(payload: Dict[str, Any]) -> Dict[str, Any]:
    msg = str(payload.get("message", ""))[:1024]
    return {"op": "echo", "message": msg}

def op_compact_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = str(payload.get("text", payload.get("prompt", "")))
    compact = " ".join(text.split())
    return {
        "op": "compact_text",
        "chars_in": len(text),
        "chars_out": len(compact),
        "text_compact": compact[:2048],
    }

# Registry: Abraxas-side definition of ops + their capability needs.
# IMPORTANT: Enforcement is done by AAL-Core via manifest op_policy.
OPS: Dict[str, OpSpec] = {
    "hash": OpSpec(fn=op_hash, required_caps=[]),
    "echo": OpSpec(fn=op_echo, required_caps=[]),
    "compact_text": OpSpec(fn=op_compact_text, required_caps=[]),
    # Future examples:
    # "render_pdf": OpSpec(fn=op_render_pdf, required_caps=["writes"]),
    # "fetch_web": OpSpec(fn=op_fetch_web, required_caps=["external_io"]),
}

def execute_ascend(payload: Dict[str, Any]) -> Dict[str, Any]:
    op = str(payload.get("op", "unspecified"))
    if op not in OPS:
        return {
            "mode": "ASCEND",
            "ok": False,
            "error": f"op not allowed: {op}",
            "allowed_ops": sorted(list(OPS.keys())),
        }

    spec = OPS[op]
    result = spec.fn(payload)

    # Include op meta (useful for debugging/audit; AAL-Core remains the gate)
    return {
        "mode": "ASCEND",
        "ok": True,
        "op": op,
        "required_caps": list(spec.required_caps),
        "result": result,
    }
