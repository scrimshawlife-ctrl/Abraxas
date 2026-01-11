"""Deterministic overlay extraction for visualization (shadow-only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _split_edge(edge: str) -> Tuple[str, str]:
    s = str(edge or "")
    if "--" not in s:
        return s, ""
    left, right = s.split("--", 1)
    left = left.strip()
    right = right.strip()
    if left <= right:
        return left, right
    return right, left


def _window_vectors_from_pressure_cells(atlas_pack: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    windows: Dict[str, Dict[str, float]] = {}
    for cell in atlas_pack.get("pressure_cells") or []:
        window = str(cell.get("window_utc") or "")
        vector = str(cell.get("vector") or "")
        if not window or not vector:
            continue
        intensity = _safe_float(cell.get("intensity"))
        if intensity is None:
            continue
        windows.setdefault(window, {})[vector] = float(intensity)
    return windows


def _bridge_edges(bridge_set: Dict[str, Any]) -> List[str]:
    edges = bridge_set.get("bridge_edges") or []
    out: List[str] = []
    for edge in edges:
        key = str(edge.get("edge") or "")
        if key:
            out.append(key)
    return sorted(set(out))


def _alert_edges(alerts: Dict[str, Any]) -> List[str]:
    edge_alerts = alerts.get("edge_alerts") or []
    out: List[str] = []
    for edge in edge_alerts:
        key = str(edge.get("edge") or "")
        if key:
            out.append(key)
    return sorted(set(out))


def build_overlay_signals(
    *,
    atlas_pack: Dict[str, Any],
    bridge_set: Optional[Dict[str, Any]] = None,
    alerts: Optional[Dict[str, Any]] = None,
    intensity_threshold: float = 0.50,
) -> Dict[str, Dict[str, float]]:
    """Return window_utc -> overlay signals for bridge + alert edges."""
    if not isinstance(atlas_pack, dict):
        atlas_pack = dict(getattr(atlas_pack, "__dict__", {}) or {})

    if bridge_set is None and alerts is None:
        return {}

    window_vectors = _window_vectors_from_pressure_cells(atlas_pack)
    bridge_edges = _bridge_edges(bridge_set or {}) if isinstance(bridge_set, dict) else []
    alert_edges = _alert_edges(alerts or {}) if isinstance(alerts, dict) else []

    overlay: Dict[str, Dict[str, float]] = {}

    def score_edges(edges: List[str], vectors: Dict[str, float]) -> float:
        if not edges:
            return 0.0
        hits = 0
        for edge in edges:
            left, right = _split_edge(edge)
            if not left or not right:
                continue
            left_val = vectors.get(left)
            right_val = vectors.get(right)
            if left_val is None or right_val is None:
                continue
            if float(left_val) >= float(intensity_threshold) and float(right_val) >= float(intensity_threshold):
                hits += 1
        denom = max(1, len(edges))
        return max(0.0, min(1.0, float(hits) / float(denom)))

    for window in sorted(window_vectors.keys()):
        vectors = window_vectors[window]
        bridge_signal = score_edges(bridge_edges, vectors) if bridge_edges else 0.0
        alert_signal = score_edges(alert_edges, vectors) if alert_edges else 0.0
        if bridge_signal == 0.0 and alert_signal == 0.0:
            continue
        overlay[window] = {"bridge_signal": float(bridge_signal), "alert_signal": float(alert_signal)}

    return overlay
