"""Influence composite scoring over TVM frames."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.core.canonical import canonical_json, sha256_hex


def compute_ics(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not frames:
        return {
            "ics": {"_global": _empty_metrics()},
            "provenance": {
                "inputs_hash": sha256_hex(canonical_json(frames)),
            },
        }

    metrics = _empty_metrics()
    metrics["not_computable"] = []
    return {
        "ics": {"_global": metrics},
        "provenance": {
            "inputs_hash": sha256_hex(canonical_json(frames)),
            "metrics": ["CVP", "TLL", "RD", "CDEC", "RRS"],
        },
    }


def _empty_metrics() -> Dict[str, Any]:
    return {
        "CVP": None,
        "TLL": None,
        "RD": None,
        "CDEC": None,
        "RRS": None,
        "not_computable": ["CVP", "TLL", "RD", "CDEC", "RRS"],
    }
