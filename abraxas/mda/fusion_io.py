from __future__ import annotations

from typing import Any, Dict, List

from .types import FusionEdge, FusionGraph


def fusiongraph_from_json(fj: Dict[str, Any]) -> FusionGraph:
    nodes = fj.get("nodes", {}) or {}
    edges_in = fj.get("edges", []) or []
    edges: List[FusionEdge] = []

    for e in edges_in:
        edges.append(
            FusionEdge(
                src_id=str(e.get("src_id")),
                dst_id=str(e.get("dst_id")),
                edge_type=str(e.get("edge_type")),
                evidence_refs=tuple(
                    str(x) for x in (e.get("evidence_refs") or []) if str(x).strip()
                ),
                weight=float(e.get("weight", 1.0)),
                notes=(None if e.get("notes") is None else str(e.get("notes"))),
            )
        )

    edges_sorted = tuple(sorted(edges, key=lambda x: (x.edge_type, x.src_id, x.dst_id)))
    return FusionGraph(nodes=nodes, edges=edges_sorted)

