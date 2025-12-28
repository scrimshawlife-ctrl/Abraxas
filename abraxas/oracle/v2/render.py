from __future__ import annotations

from typing import Any, Dict, List


def _safe_get(d: Dict[str, Any], path: List[str], default: Any) -> Any:
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def render_snapshot(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic snapshot projection.
    Economy: uses v1 top lists; does not surface evidence blobs.
    """
    sig = envelope.get("oracle_signal", {}) or {}
    window = sig.get("window")
    v1 = sig.get("scores_v1", {}) or {}
    slang = v1.get("slang", {}) or {}
    aal = v1.get("aalmanac", {}) or {}
    v2 = sig.get("v2", {}) or {}
    compliance = v2.get("compliance", {}) or {}

    top_vital = slang.get("top_vital", []) if isinstance(slang.get("top_vital", []), list) else []
    top_risk = slang.get("top_risk", []) if isinstance(slang.get("top_risk", []), list) else []
    top_patterns = aal.get("top_patterns", []) if isinstance(aal.get("top_patterns", []), list) else []

    # Keep snapshot bounded and deterministic
    def _take(xs, n):  # stable slice only
        return xs[:n] if isinstance(xs, list) else []

    return {
        "mode": "SNAPSHOT",
        "window": window,
        "status": compliance.get("status"),
        "top_slang_vital": _take(top_vital, 10),
        "top_slang_risk": _take(top_risk, 10),
        "top_patterns": _take(top_patterns, 10),
        "provenance": {"config_hash": _safe_get(compliance, ["provenance", "config_hash"], None)},
    }


def render_analyst(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyst view: full envelope passthrough (debug posture).
    """
    sig = envelope.get("oracle_signal", {}) or {}
    v2 = sig.get("v2", {}) or {}
    compliance = v2.get("compliance", {}) or {}
    return {
        "mode": "ANALYST",
        "envelope": envelope,
        "provenance": {"config_hash": _safe_get(compliance, ["provenance", "config_hash"], None)},
    }


def render_ritual(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ritual shell: symbolic projection container. No auto-selection.
    """
    sig = envelope.get("oracle_signal", {}) or {}
    window = sig.get("window")
    v2 = sig.get("v2", {}) or {}
    compliance = v2.get("compliance", {}) or {}
    # Minimal sigil placeholder. Real sigil generation stays elsewhere.
    return {
        "mode": "RITUAL",
        "window": window,
        "sigils": [],
        "anchors": [],
        "disclaimer": "Symbolic projection only; non-authoritative; no back-propagation into metrics.",
        "provenance": {"config_hash": _safe_get(compliance, ["provenance", "config_hash"], None)},
    }


def render_by_mode(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Single switch that respects the locked v2 mode.
    """
    mode = _safe_get(envelope, ["oracle_signal", "v2", "mode"], "SNAPSHOT")
    if mode == "ANALYST":
        return render_analyst(envelope)
    if mode == "RITUAL":
        return render_ritual(envelope)
    return render_snapshot(envelope)
