"""Exporters for live atlas packs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from abraxas.live.schema import LiveAtlasPack


def export_live_json(live_pack: LiveAtlasPack, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(live_pack.model_dump(), indent=2, sort_keys=True), encoding="utf-8")


def export_live_trendpack(live_pack: LiveAtlasPack) -> Dict[str, Any]:
    series: Dict[str, List[Dict[str, Any]]] = {}
    for window_pack in live_pack.windows:
        for cell in window_pack.get("pressure_cells") or []:
            vector = cell.get("vector")
            series.setdefault(vector, []).append(
                {
                    "window_utc": cell.get("window_utc"),
                    "intensity": cell.get("intensity"),
                    "gradient": cell.get("gradient"),
                }
            )
    for vector in series:
        series[vector] = sorted(series[vector], key=lambda item: item["window_utc"])
    return {
        "live_version": live_pack.live_version,
        "generated_at_utc": live_pack.generated_at_utc,
        "window_config": live_pack.window_config,
        "series": series,
    }


def export_latest_snapshot(live_pack: LiveAtlasPack) -> Dict[str, Any]:
    if not live_pack.windows:
        return {}
    return live_pack.windows[-1]
