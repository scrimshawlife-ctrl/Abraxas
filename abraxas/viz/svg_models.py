from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 800
ARTIFACT_ID = "AAL-VIZ-CANARY-SVG-RENDERER-001"
MANIFEST_SCHEMA_VERSION = "AALVizCanarySVGRenderManifest.v1"

AUTHORITY_FLAGS = {
    "svg_rendering": True,
    "viz_projection": True,
    "inference": False,
    "production_activation": False,
    "baseline_mutation": False,
    "runtime_config_write": False,
    "promotion": False,
    "execution": False,
    "scheduler": False,
}


@dataclass(frozen=True)
class RenderCounts:
    nodes: int
    edges: int
    alerts: int
    actions: int

    def to_dict(self) -> Dict[str, int]:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "alerts": self.alerts,
            "actions": self.actions,
        }


def extract_view_id(view_packet: Dict[str, Any]) -> str:
    return str(view_packet.get("view_id") or view_packet.get("id") or "")


def extract_counts(view_packet: Dict[str, Any]) -> RenderCounts:
    nodes = list(view_packet.get("nodes") or [])
    edges = list(view_packet.get("edges") or [])
    alerts = list(view_packet.get("alerts") or [])
    actions = list(view_packet.get("actions") or [])
    return RenderCounts(nodes=len(nodes), edges=len(edges), alerts=len(alerts), actions=len(actions))


def manifest_payload(
    *,
    render_id: str,
    view_id: str,
    svg_hash: str,
    view_packet_hash: str,
    counts: RenderCounts,
    svg_path: str,
) -> Dict[str, Any]:
    return {
        "artifact": ARTIFACT_ID,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "render_id": render_id,
        "view_id": view_id,
        "svg_hash": svg_hash,
        "view_packet_hash": view_packet_hash,
        "dimensions": {"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT},
        "counts": counts.to_dict(),
        "files": {"svg_path": svg_path},
        "authority": dict(AUTHORITY_FLAGS),
    }
