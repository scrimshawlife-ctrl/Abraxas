"""Atlas exporters for downstream visualization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from abraxas.atlas.schema import AtlasPack


def export_json(atlas_pack: AtlasPack, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(atlas_pack.model_dump(), indent=2, sort_keys=True), encoding="utf-8")


def export_trendpack(atlas_pack: AtlasPack) -> Dict[str, Any]:
    series: Dict[str, List[Dict[str, Any]]] = {}
    for cell in atlas_pack.pressure_cells:
        vector = cell["vector"]
        window_start, window_end = _split_window(cell["window_utc"])
        series.setdefault(vector, []).append(
            {
                "window_start_utc": window_start,
                "window_end_utc": window_end,
                "intensity": cell.get("intensity"),
                "gradient": cell.get("gradient"),
            }
        )
    for vector in series:
        series[vector] = sorted(series[vector], key=lambda item: item["window_start_utc"])
    return {
        "atlas_version": atlas_pack.atlas_version,
        "year": atlas_pack.year,
        "window_granularity": atlas_pack.window_granularity,
        "series": series,
    }


def export_chronoscope(atlas_pack: AtlasPack) -> Dict[str, Any]:
    window_map: Dict[str, Dict[str, Any]] = {}
    for cell in atlas_pack.pressure_cells:
        window_id = cell["window_utc"]
        window_start, window_end = _split_window(window_id)
        entry = window_map.setdefault(
            window_id,
            {"window_start_utc": window_start, "window_end_utc": window_end, "vectors": {}, "gradients": {}},
        )
        entry["vectors"][cell["vector"]] = cell.get("intensity")
        entry["gradients"][cell["vector"]] = cell.get("gradient")

    windows = sorted(window_map.values(), key=lambda item: item["window_start_utc"])
    return {
        "atlas_version": atlas_pack.atlas_version,
        "year": atlas_pack.year,
        "window_granularity": atlas_pack.window_granularity,
        "windows": windows,
        "jetstreams": atlas_pack.jetstreams,
        "cyclones": atlas_pack.cyclones,
        "calm_zones": atlas_pack.calm_zones,
        "synchronicity_clusters": atlas_pack.synchronicity_clusters,
    }


def _split_window(window_utc: str) -> Tuple[str, str]:
    parts = window_utc.split("/")
    if len(parts) == 2:
        return parts[0], parts[1]
    return window_utc, ""
