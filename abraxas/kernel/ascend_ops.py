# =========================
# FILE: abraxas/kernel/ascend_ops.py
# PURPOSE: Whitelisted ASCEND operations (deterministic, side-effect-free by default)
# =========================

from __future__ import annotations
from typing import Any, Dict, Callable
import json
import hashlib

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def op_hash(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Deterministic hashing utility
    value = payload.get("value", "")
    s = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    return {"op": "hash", "sha256": _sha256(s)}

def op_echo(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Deterministic echo (bounded)
    msg = str(payload.get("message", ""))[:1024]
    return {"op": "echo", "message": msg}

def op_compact_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Pure text normalization (bounded)
    text = str(payload.get("text", payload.get("prompt", "")))
    compact = " ".join(text.split())
    return {
        "op": "compact_text",
        "chars_in": len(text),
        "chars_out": len(compact),
        "text_compact": compact[:2048],
    }

# Whitelist registry: ONLY these ops can run in ASCEND until you expand intentionally.
OPS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "hash": op_hash,
    "echo": op_echo,
    "compact_text": op_compact_text,
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
    result = OPS[op](payload)
    return {"mode": "ASCEND", "ok": True, "result": result}
