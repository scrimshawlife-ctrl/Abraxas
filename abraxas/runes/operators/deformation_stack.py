from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

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


class DeformationParams(BaseModel):
    top_k_edges_considered: int = Field(default=200)
    bridge_edge_min_score: float = Field(default=0.35)
    bridge_edge_min_persistence: int = Field(default=3)
    bridge_node_min_degree: int = Field(default=2)
    alert_min_score_delta: float = Field(default=0.10)
    alert_min_persistence_delta: int = Field(default=1)
    alert_top_k: int = Field(default=50)


def _index_edges(edges: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for edge in edges or []:
        key = str(edge.get("edge") or "")
        if key:
            index[key] = edge
    return index


def _index_clusters(clusters: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for cluster in clusters or []:
        cid = str(cluster.get("cluster_id") or "")
        if cid:
            index[cid] = cluster
    return index


def apply_deformation_stack(
    *,
    watchlist: Dict[str, Any],
    prev_watchlist: Optional[Dict[str, Any]] = None,
    params: Optional[DeformationParams] = None,
) -> Dict[str, Dict[str, Any]]:
    """Deformation Stack v0.1 (shadow-only)."""
    params = params or DeformationParams()
    if hasattr(watchlist, "model_dump"):
        watchlist = watchlist.model_dump()
    if prev_watchlist is not None and hasattr(prev_watchlist, "model_dump"):
        prev_watchlist = prev_watchlist.model_dump()

    edges = watchlist.get("edges_top") or []
    clusters = watchlist.get("clusters_top") or []

    provenance_base = {
        "shadow_only": True,
        "operator": "deformation_stack",
        "params": params.model_dump(),
        "watchlist_hash": watchlist.get("watchlist_hash") or _canon_hash(watchlist),
        "prev_watchlist_hash": (prev_watchlist or {}).get("watchlist_hash")
        if isinstance(prev_watchlist, dict)
        else None,
    }

    considered = edges[: max(0, int(params.top_k_edges_considered))]
    candidates: List[Dict[str, Any]] = []
    for edge in considered:
        score = _safe_float(edge.get("score")) or 0.0
        persistence = int(edge.get("persistence") or 0)
        if score < float(params.bridge_edge_min_score):
            continue
        if persistence < int(params.bridge_edge_min_persistence):
            continue
        candidates.append(
            {
                "edge": str(edge.get("edge") or ""),
                "score": float(score),
                "persistence": persistence,
                "mean_density": float(_safe_float(edge.get("mean_density")) or 0.0),
                "mean_intensity": float(_safe_float(edge.get("mean_intensity")) or 0.0),
            }
        )

    degrees: Dict[str, int] = {}
    for edge in candidates:
        left, right = _split_edge(edge["edge"])
        if left:
            degrees[left] = degrees.get(left, 0) + 1
        if right:
            degrees[right] = degrees.get(right, 0) + 1

    bridge_edges: List[Dict[str, Any]] = []
    for edge in candidates:
        left, right = _split_edge(edge["edge"])
        if degrees.get(left, 0) >= int(params.bridge_node_min_degree) or degrees.get(right, 0) >= int(
            params.bridge_node_min_degree
        ):
            bridge_edges.append(edge)

    bridge_nodes = [
        {"motif": node, "degree": int(degree)}
        for node, degree in sorted(degrees.items(), key=lambda item: (-item[1], item[0]))
        if degree >= int(params.bridge_node_min_degree)
    ]

    bridge_set = {
        "schema_version": "bridge_set.v0.1",
        "shadow_only": True,
        "not_computable": False if (bridge_edges or bridge_nodes) else True,
        "bridge_nodes": bridge_nodes,
        "bridge_edges": sorted(bridge_edges, key=lambda record: (-record["score"], -record["persistence"], record["edge"])),
        "provenance": dict(provenance_base, stage="bridge_set"),
    }
    bridge_set["bridge_set_hash"] = _canon_hash(bridge_set)

    alerts_edges: List[Dict[str, Any]] = []
    alerts_clusters: List[Dict[str, Any]] = []
    if isinstance(prev_watchlist, dict):
        prev_edges = _index_edges(prev_watchlist.get("edges_top") or [])
        prev_clusters = _index_clusters(prev_watchlist.get("clusters_top") or [])
        curr_edges = _index_edges(edges)
        curr_clusters = _index_clusters(clusters)

        for key in sorted(curr_edges.keys()):
            cur = curr_edges[key]
            prev = prev_edges.get(key)
            if prev is None:
                score_delta = float(_safe_float(cur.get("score")) or 0.0)
                persistence_delta = int(cur.get("persistence") or 0)
                if score_delta >= float(params.alert_min_score_delta) or persistence_delta >= int(
                    params.alert_min_persistence_delta
                ):
                    alerts_edges.append(
                        {
                            "edge": key,
                            "type": "new",
                            "score_delta": score_delta,
                            "persistence_delta": persistence_delta,
                        }
                    )
                continue
            score_cur = float(_safe_float(cur.get("score")) or 0.0)
            score_prev = float(_safe_float(prev.get("score")) or 0.0)
            persistence_cur = int(cur.get("persistence") or 0)
            persistence_prev = int(prev.get("persistence") or 0)
            score_delta = score_cur - score_prev
            persistence_delta = persistence_cur - persistence_prev
            if score_delta >= float(params.alert_min_score_delta) or persistence_delta >= int(
                params.alert_min_persistence_delta
            ):
                alerts_edges.append(
                    {
                        "edge": key,
                        "type": "delta",
                        "score_delta": score_delta,
                        "persistence_delta": persistence_delta,
                    }
                )

        for cid in sorted(curr_clusters.keys()):
            cur = curr_clusters[cid]
            prev = prev_clusters.get(cid)
            density_cur = float(_safe_float(cur.get("density_score")) or 0.0)
            density_prev = float(_safe_float(prev.get("density_score")) or 0.0) if prev else 0.0
            density_delta = density_cur - density_prev
            if density_delta >= float(params.alert_min_score_delta):
                alerts_clusters.append(
                    {
                        "cluster_id": cid,
                        "type": "delta" if prev else "new",
                        "density_delta": density_delta,
                    }
                )

    alerts_edges.sort(
        key=lambda record: (-(record.get("score_delta") or 0.0), -(record.get("persistence_delta") or 0), record["edge"])
    )
    alerts_clusters.sort(key=lambda record: (-(record.get("density_delta") or 0.0), record["cluster_id"]))

    alerts = {
        "schema_version": "watchlist_alerts.v0.1",
        "shadow_only": True,
        "not_computable": False if (alerts_edges or alerts_clusters) else True,
        "edge_alerts": alerts_edges[: max(0, int(params.alert_top_k))],
        "cluster_alerts": alerts_clusters[: max(0, int(params.alert_top_k))],
        "provenance": dict(provenance_base, stage="alerts"),
    }
    alerts["alerts_hash"] = _canon_hash(alerts)

    report = {
        "schema_version": "deformation_report.v0.1",
        "shadow_only": True,
        "not_computable": False,
        "summary": {
            "edges_considered": int(len(considered)),
            "bridge_edges": int(len(bridge_edges)),
            "bridge_nodes": int(len(bridge_nodes)),
            "edge_alerts": int(len(alerts_edges)),
            "cluster_alerts": int(len(alerts_clusters)),
        },
        "provenance": dict(provenance_base, stage="report"),
    }
    report["report_hash"] = _canon_hash(report)

    return {"bridge_set": bridge_set, "alerts": alerts, "report": report}
