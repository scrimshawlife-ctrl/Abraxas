"""Deformation stack CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from abraxas.runes.operators.deformation_stack import DeformationParams, apply_deformation_stack


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_deform_cmd(
    watchlist_path: str,
    bridge_out: str,
    alerts_out: str,
    report_out: str,
    prev_watchlist_path: str | None = None,
    top_k_edges_considered: int = 200,
    bridge_min_score: float = 0.35,
    bridge_min_persistence: int = 3,
    bridge_node_min_degree: int = 2,
    alert_min_score_delta: float = 0.10,
    alert_min_persistence_delta: int = 1,
    alert_top_k: int = 50,
) -> int:
    watchlist = _read_json(Path(watchlist_path))
    prev = _read_json(Path(prev_watchlist_path)) if prev_watchlist_path else None

    params = DeformationParams(
        top_k_edges_considered=top_k_edges_considered,
        bridge_edge_min_score=bridge_min_score,
        bridge_edge_min_persistence=bridge_min_persistence,
        bridge_node_min_degree=bridge_node_min_degree,
        alert_min_score_delta=alert_min_score_delta,
        alert_min_persistence_delta=alert_min_persistence_delta,
        alert_top_k=alert_top_k,
    )

    out = apply_deformation_stack(watchlist=watchlist, prev_watchlist=prev, params=params)
    _write_json(Path(bridge_out), out["bridge_set"])
    _write_json(Path(alerts_out), out["alerts"])
    _write_json(Path(report_out), out["report"])
    return 0


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
