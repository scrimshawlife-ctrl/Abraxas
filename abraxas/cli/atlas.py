"""Atlas export CLI."""

from __future__ import annotations

import json
from pathlib import Path

from abraxas.atlas.construct import build_atlas_pack, load_seedpack
from abraxas.atlas.export import export_chronoscope, export_trendpack
from abraxas.runes.operators.atlas_coupling_watchlist import (
    CouplingWatchlistParams,
    apply_atlas_coupling_watchlist,
)
from abraxas.runes.operators.atlas_synch_cluster import (
    AtlasSynchClusterParams,
    apply_atlas_synch_cluster,
)


def run_atlas_cmd(
    year: int,
    window: str,
    seed_path: str,
    out_path: str,
    trendpack_path: str | None = None,
    chronoscope_path: str | None = None,
    attach_synch_clusters: bool = False,
    synch_seed: int = 133742,
    synch_min_strength: float = 0.15,
    synch_top_k: int = 50,
    coupling_watchlist_out: str | None = None,
    watchlist_top_k_edges: int = 200,
    watchlist_top_k_clusters: int = 100,
    watchlist_min_persistence: int = 2,
) -> int:
    seedpack = load_seedpack(Path(seed_path))
    seed_year = int(seedpack.get("year") or 0)
    if seed_year and seed_year != year:
        raise SystemExit(f"Seedpack year {seed_year} does not match requested year {year}")
    atlas_pack = build_atlas_pack(seedpack, window_granularity=window)

    payload = atlas_pack.model_dump()
    if attach_synch_clusters:
        params = AtlasSynchClusterParams(
            seed=synch_seed,
            min_strength=synch_min_strength,
            top_k=synch_top_k,
        )
        payload["synchronicity_clustered"] = apply_atlas_synch_cluster(payload, params)
    if coupling_watchlist_out:
        params = CouplingWatchlistParams(
            top_k_edges=watchlist_top_k_edges,
            top_k_clusters=watchlist_top_k_clusters,
            min_persistence=watchlist_min_persistence,
        )
        watchlist = apply_atlas_coupling_watchlist(payload, params)
        out_path_obj = Path(coupling_watchlist_out)
        out_path_obj.parent.mkdir(parents=True, exist_ok=True)
        out_path_obj.write_text(json.dumps(watchlist, indent=2, sort_keys=True), encoding="utf-8")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    if trendpack_path:
        trendpack = export_trendpack(atlas_pack)
        Path(trendpack_path).parent.mkdir(parents=True, exist_ok=True)
        Path(trendpack_path).write_text(json.dumps(trendpack, indent=2, sort_keys=True), encoding="utf-8")
    if chronoscope_path:
        chronoscope = export_chronoscope(atlas_pack)
        Path(chronoscope_path).parent.mkdir(parents=True, exist_ok=True)
        Path(chronoscope_path).write_text(json.dumps(chronoscope, indent=2, sort_keys=True), encoding="utf-8")
    return 0
