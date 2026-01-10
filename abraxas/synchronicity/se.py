"""Synchronicity envelope computation."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.core.canonical import canonical_json, sha256_hex


def compute_se(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    payload = {
        "envelopes": [],
        "not_computable": True if not frames else False,
        "provenance": {
            "inputs_hash": sha256_hex(canonical_json(frames)),
        },
    }
    return payload
