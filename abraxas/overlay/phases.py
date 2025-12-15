from __future__ import annotations
from typing import Any, Dict
from .schema import Phase

def handle_open(payload: Dict[str, Any]) -> Dict[str, Any]:
    prompt = str(payload.get("prompt", ""))
    intent = str(payload.get("intent", "unspecified"))
    return {
        "mode": "OPEN",
        "intent": intent,
        "signal": "intake_ok",
        "prompt_len": len(prompt),
    }

def handle_align(payload: Dict[str, Any]) -> Dict[str, Any]:
    op = str(payload.get("op", payload.get("intent", "unspecified")))
    return {
        "mode": "ALIGN",
        "op": op,
        "constraints": {
            "determinism": True,
            "provenance": True,
            "no_mock_data": True,
        },
    }

def handle_clear(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = str(payload.get("text", payload.get("prompt", "")))
    compact = " ".join(text.split())
    return {
        "mode": "CLEAR",
        "compression": {
            "chars_in": len(text),
            "chars_out": len(compact),
            "ratio": (len(compact) / len(text)) if len(text) else 1.0,
        },
        "text_compact": compact[:512],
    }

def handle_seal(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = str(payload.get("title", "Abraxas Artifact"))
    return {
        "mode": "SEAL",
        "artifact": {
            "title": title,
            "status": "sealed_stub",
        }
    }

def dispatch(phase: Phase, payload: Dict[str, Any]) -> Dict[str, Any]:
    if phase == "OPEN":
        return handle_open(payload)
    if phase == "ALIGN":
        return handle_align(payload)
    if phase == "CLEAR":
        return handle_clear(payload)
    if phase == "SEAL":
        return handle_seal(payload)
    if phase == "ASCEND":
        return {"mode": "ASCEND", "note": "ASCEND handler not enabled in overlay yet"}
    raise ValueError(f"Unsupported phase: {phase}")
