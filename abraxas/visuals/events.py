"""Overlay events emission for visualization (shadow-only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.core.canonical import canonical_json, sha256_hex


def _canon_hash(obj: Dict[str, Any]) -> str:
    return sha256_hex(canonical_json(obj))


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def emit_overlay_events(
    *,
    bridge_set: Optional[Dict[str, Any]] = None,
    alerts: Optional[Dict[str, Any]] = None,
    atlas_pack: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build OverlayEvents.v0.1 deterministically (shadow-only)."""
    bridge_set = bridge_set if isinstance(bridge_set, dict) else None
    alerts = alerts if isinstance(alerts, dict) else None
    atlas_pack = atlas_pack if isinstance(atlas_pack, dict) else None

    provenance = {
        "shadow_only": True,
        "operator": "overlay_events",
        "bridge_set_hash": (bridge_set or {}).get("bridge_set_hash") if bridge_set else None,
        "alerts_hash": (alerts or {}).get("alerts_hash") if alerts else None,
        "atlas_hash": (atlas_pack or {}).get("atlas_hash") if atlas_pack else None,
    }

    events: List[Dict[str, Any]] = []

    if bridge_set:
        for edge in bridge_set.get("bridge_edges") or []:
            edge_key = str(edge.get("edge") or "")
            if not edge_key:
                continue
            score = _safe_float(edge.get("score"))
            if score is None:
                score = 0.0
            events.append(
                {
                    "window_utc": "*",
                    "kind": "bridge_edge",
                    "entity_id": edge_key,
                    "magnitude": _clamp01(float(score)),
                    "payload": {
                        "persistence": int(edge.get("persistence") or 0),
                        "mean_density": float(_safe_float(edge.get("mean_density")) or 0.0),
                        "mean_intensity": float(_safe_float(edge.get("mean_intensity")) or 0.0),
                    },
                    "provenance_refs": [],
                }
            )

    if alerts:
        for alert in alerts.get("edge_alerts") or []:
            edge_key = str(alert.get("edge") or "")
            if not edge_key:
                continue
            score_delta = float(_safe_float(alert.get("score_delta")) or 0.0)
            persistence_delta = int(alert.get("persistence_delta") or 0)
            magnitude = _clamp01(score_delta + min(0.25, 0.05 * float(max(0, persistence_delta))))
            events.append(
                {
                    "window_utc": "*",
                    "kind": "edge_alert",
                    "entity_id": edge_key,
                    "magnitude": magnitude,
                    "payload": {
                        "type": str(alert.get("type") or "delta"),
                        "score_delta": score_delta,
                        "persistence_delta": persistence_delta,
                    },
                    "provenance_refs": [],
                }
            )
        for alert in alerts.get("cluster_alerts") or []:
            cluster_id = str(alert.get("cluster_id") or "")
            if not cluster_id:
                continue
            density_delta = float(_safe_float(alert.get("density_delta")) or 0.0)
            events.append(
                {
                    "window_utc": "*",
                    "kind": "cluster_alert",
                    "entity_id": cluster_id,
                    "magnitude": _clamp01(density_delta),
                    "payload": {
                        "type": str(alert.get("type") or "delta"),
                        "density_delta": density_delta,
                    },
                    "provenance_refs": [],
                }
            )

    if atlas_pack and events:
        cluster_windows: Dict[str, str] = {}
        for cluster in atlas_pack.get("synchronicity_clusters") or []:
            cluster_id = str(cluster.get("cluster_id") or "")
            time_window = str(cluster.get("time_window") or "")
            if cluster_id and time_window:
                cluster_windows[cluster_id] = time_window
        for event in events:
            if event["kind"] == "cluster_alert":
                mapped_window = cluster_windows.get(event["entity_id"])
                if mapped_window:
                    event["window_utc"] = mapped_window

    events.sort(key=lambda event: (event["window_utc"], event["kind"], -float(event["magnitude"]), event["entity_id"]))

    out = {
        "schema_version": "overlay_events.v0.1",
        "shadow_only": True,
        "not_computable": False if events else True,
        "events": events,
        "provenance": provenance,
    }
    out["events_hash"] = _canon_hash(out)
    return out
