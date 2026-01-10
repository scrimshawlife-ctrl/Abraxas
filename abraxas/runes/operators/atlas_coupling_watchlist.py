from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


def _canon_hash(obj: Dict[str, Any]) -> str:
    return sha256_hex(canonical_json(obj))


class CouplingWatchlistParams(BaseModel):
    top_k_edges: int = Field(default=200)
    top_k_clusters: int = Field(default=100)
    min_persistence: int = Field(default=2)
    min_density: float = Field(default=0.0)
    w_persistence: float = Field(default=0.50)
    w_density: float = Field(default=0.30)
    w_intensity: float = Field(default=0.20)


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stable_mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / float(len(values))


def apply_atlas_coupling_watchlist(
    atlas: Dict[str, Any], params: Optional[CouplingWatchlistParams] = None
) -> Dict[str, Any]:
    """Build a deterministic coupling watchlist from atlas topology (shadow-only)."""
    params = params or CouplingWatchlistParams()

    if hasattr(atlas, "model_dump"):
        atlas = atlas.model_dump()
    elif not isinstance(atlas, dict):
        atlas = dict(getattr(atlas, "__dict__", {}) or {})

    pressure_cells = atlas.get("pressure_cells") or []
    clusters = atlas.get("synchronicity_clusters") or []

    provenance = {
        "operator": "atlas_coupling_watchlist",
        "shadow_only": True,
        "params": params.model_dump(),
        "atlas_hash": _canon_hash(atlas),
        "atlas_version": atlas.get("atlas_version") or atlas.get("schema_version"),
        "year": atlas.get("year"),
        "window": atlas.get("window_granularity") or atlas.get("window"),
    }

    if not pressure_cells and not clusters:
        out = {
            "schema_version": "coupling_watchlist.v0.1",
            "shadow_only": True,
            "not_computable": True,
            "edges_top": [],
            "clusters_top": [],
            "domain_pairs": [],
            "provenance": provenance,
        }
        out["watchlist_hash"] = _canon_hash(out)
        return out

    density_by_window: Dict[str, float] = {}
    for cluster in clusters:
        time_window = str(cluster.get("time_window") or "")
        density = _safe_float(cluster.get("density_score"))
        if time_window and density is not None:
            density_by_window[time_window] = max(density_by_window.get(time_window, 0.0), density)

    edge_obs: Dict[str, Dict[str, Any]] = {}
    for cell in pressure_cells:
        window = str(cell.get("window_utc") or "")
        intensity = _safe_float(cell.get("intensity"))
        edges = cell.get("motif_edges") or []
        if not isinstance(edges, list):
            continue
        density = density_by_window.get(window)
        for edge in edges:
            key = str(edge or "")
            if not key:
                continue
            rec = edge_obs.setdefault(key, {"windows": set(), "intensity_vals": [], "density_vals": []})
            if window:
                rec["windows"].add(window)
            if intensity is not None:
                rec["intensity_vals"].append(float(intensity))
            if density is not None:
                rec["density_vals"].append(float(density))

    edges_ranked: List[Dict[str, Any]] = []
    for edge, rec in edge_obs.items():
        persistence = int(len(rec["windows"]))
        if persistence < int(params.min_persistence):
            continue
        mean_intensity = _stable_mean(rec["intensity_vals"]) or 0.0
        mean_density = _stable_mean(rec["density_vals"]) or 0.0
        if mean_density < float(params.min_density):
            continue

        p_norm = min(1.0, float(persistence) / 10.0)
        d_norm = max(0.0, min(1.0, float(mean_density)))
        i_norm = max(0.0, min(1.0, float(mean_intensity)))
        score = (
            float(params.w_persistence) * p_norm
            + float(params.w_density) * d_norm
            + float(params.w_intensity) * i_norm
        )

        edges_ranked.append(
            {
                "edge": edge,
                "persistence": persistence,
                "mean_density": d_norm,
                "mean_intensity": i_norm,
                "score": score,
            }
        )

    edges_ranked.sort(key=lambda record: (-record["score"], -record["persistence"], record["edge"]))
    edges_ranked = edges_ranked[: max(0, int(params.top_k_edges))]

    clusters_ranked: List[Dict[str, Any]] = []
    for cluster in clusters:
        cluster_id = str(cluster.get("cluster_id") or "")
        density_score = _safe_float(cluster.get("density_score"))
        if density_score is None:
            density_score = 0.0
        time_window = str(cluster.get("time_window") or "")
        domains = cluster.get("domains") or []
        vectors = cluster.get("vectors") or []
        persistence = 1
        score = max(0.0, min(1.0, float(density_score))) * min(1.0, float(persistence) / 10.0)
        clusters_ranked.append(
            {
                "cluster_id": cluster_id,
                "time_window": time_window,
                "density_score": max(0.0, min(1.0, float(density_score))),
                "domains": list(sorted({str(d) for d in domains if isinstance(d, str)})),
                "vectors": list(sorted({str(v) for v in vectors if isinstance(v, str)})),
                "persistence": persistence,
                "score": score,
            }
        )

    clusters_ranked.sort(key=lambda record: (-record["score"], record["cluster_id"]))
    clusters_ranked = clusters_ranked[: max(0, int(params.top_k_clusters))]

    domain_pairs: Dict[str, int] = {}
    for record in clusters_ranked:
        domains = record.get("domains") or []
        if len(domains) >= 2:
            domains = sorted(domains)
            for idx in range(len(domains) - 1):
                key = f"{domains[idx]}↔{domains[idx + 1]}"
                domain_pairs[key] = domain_pairs.get(key, 0) + 1

    domain_pairs_list = [{"pair": key, "count": domain_pairs[key]} for key in sorted(domain_pairs.keys())]

    out = {
        "schema_version": "coupling_watchlist.v0.1",
        "shadow_only": True,
        "not_computable": False if (edges_ranked or clusters_ranked) else True,
        "edges_top": edges_ranked,
        "clusters_top": clusters_ranked,
        "domain_pairs": domain_pairs_list,
        "provenance": provenance,
    }
    out["watchlist_hash"] = _canon_hash(out)
    return out
