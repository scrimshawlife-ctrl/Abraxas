"""Exporters for delta atlas packs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from abraxas.atlas.delta_schema import DeltaAtlasPack


def export_delta_json(delta_pack: DeltaAtlasPack, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(delta_pack.model_dump(), indent=2, sort_keys=True), encoding="utf-8")


def export_delta_trendpack(delta_pack: DeltaAtlasPack) -> Dict[str, Any]:
    series: Dict[str, List[Dict[str, Any]]] = {}
    for item in delta_pack.delta_pressures:
        vector = item["vector"]
        window_utc = item["window_utc"]
        series.setdefault(vector, []).append(
            {
                "window_utc": window_utc,
                "delta_intensity": item.get("delta_intensity"),
                "delta_gradient": item.get("delta_gradient"),
            }
        )
    for vector in series:
        series[vector] = sorted(series[vector], key=lambda entry: entry["window_utc"])
    return {
        "delta_version": delta_pack.delta_version,
        "comparison_label": delta_pack.comparison_label,
        "window_granularity": delta_pack.window_granularity,
        "series": series,
    }
