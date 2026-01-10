from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.runes.operators.synchronicity_map import SynchronicityBundle, SynchronicityCluster


class AtlasSynchClusterParams(BaseModel):
    seed: int = Field(default=133742)
    min_strength: float = Field(default=0.15)
    top_k: int = Field(default=50)


def _edge_key(a: str, b: str) -> str:
    return f"{a}→{b}"


def apply_atlas_synch_cluster(atlas: Dict[str, Any], params: Optional[AtlasSynchClusterParams] = None) -> Dict[str, Any]:
    """Topology-aware synchronicity clustering (shadow-only)."""
    params = params or AtlasSynchClusterParams()

    jetstreams = atlas.get("jetstreams") or []
    pressure_cells = atlas.get("pressure_cells") or []
    year = atlas.get("year")
    window = atlas.get("window_granularity") or atlas.get("window")

    prov = {
        "operator": "atlas_synch_cluster",
        "shadow_only": True,
        "params": params.model_dump(),
        "atlas_hash": sha256_hex(canonical_json(atlas)),
        "year": year,
        "window": window,
    }

    if not jetstreams and not pressure_cells:
        bundle = SynchronicityBundle(
            stage="clustered",
            clusters=[],
            envelopes=[],
            not_computable=True,
            provenance=prov,
        )
        return bundle.model_dump()

    edge_scores: Dict[str, float] = {}

    for js in jetstreams:
        src = js.get("source_motif") or js.get("src") or js.get("from")
        dst = js.get("target_motif") or js.get("dst") or js.get("to")
        strength = js.get("strength") or js.get("score") or 0.0
        if isinstance(src, str) and isinstance(dst, str):
            key = _edge_key(src, dst)
            try:
                score = float(strength)
            except (TypeError, ValueError):
                score = 0.0
            edge_scores[key] = max(edge_scores.get(key, 0.0), abs(score))

    if not edge_scores:
        for cell in pressure_cells:
            motifs = cell.get("motifs") or cell.get("motif_ids") or []
            if isinstance(motifs, list):
                motifs = sorted(m for m in motifs if isinstance(m, str))
                for i in range(len(motifs) - 1):
                    key = _edge_key(motifs[i], motifs[i + 1])
                    edge_scores[key] = max(edge_scores.get(key, 0.0), 0.10)

    ranked: List[Tuple[str, float]] = sorted(edge_scores.items(), key=lambda kv: (-kv[1], kv[0]))
    ranked = ranked[: max(0, int(params.top_k))]

    clusters: List[SynchronicityCluster] = []
    by_src: Dict[str, List[Tuple[str, float]]] = {}
    for edge, score in ranked:
        src = edge.split("→", 1)[0]
        by_src.setdefault(src, []).append((edge, score))

    for src, items in sorted(by_src.items(), key=lambda kv: kv[0]):
        strength = sum(score for _, score in items) / max(1, len(items))
        if strength < params.min_strength:
            continue
        motifs = sorted({src} | {edge.split("→", 1)[1] for edge, _ in items})
        edges = [edge for edge, _ in items]
        cluster_id = sha256_hex(canonical_json({"seed": params.seed, "src": src, "edges": edges}))[:16]
        clusters.append(
            SynchronicityCluster(
                cluster_id=cluster_id,
                domain="unknown",
                motifs=motifs,
                edges=edges,
                strength=float(strength),
                provenance={"atlas_edge_count": len(items)},
            )
        )

    bundle = SynchronicityBundle(
        stage="clustered",
        clusters=clusters,
        envelopes=[],
        not_computable=(len(clusters) == 0),
        provenance=prov,
    )
    return bundle.model_dump()
