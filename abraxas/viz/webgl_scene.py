from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.webgl_scene_models import ARTIFACT, AUTHORITY, MATERIALS, SCHEMA_VERSION, default_layout
from abraxas.viz.webgl_scene_validator import validate_authority, validate_input


STATE_TOKEN_MAP = {"stable": "stable", "needs_attention": "warning", "critical": "critical"}


def _node_id(source_key: str, node_type: str, index: int) -> str:
    return sha256_hex(f"{source_key}|{node_type}|{index}")


def _edge_id(source: str, target: str) -> str:
    return sha256_hex(f"{source}|{target}")


def _position(index: int, grid_width: int, spacing: float) -> List[float]:
    x = (index % grid_width) * spacing
    y = (index // grid_width) * spacing
    return [float(x), float(y)]


def build_scene_spec(view_packet: Dict[str, Any]) -> Dict[str, Any]:
    validate_authority()
    validate_input(view_packet)
    packet = deepcopy(view_packet)

    raw_lifecycle_state = packet.get("lifecycle_state")
    alerts = list(packet.get("alerts") or [])
    actions = list(packet.get("actions") or [])

    if raw_lifecycle_state is None and not alerts and not actions:
        return {
            "artifact": ARTIFACT,
            "schema_version": SCHEMA_VERSION,
            "status": "NOT_COMPUTABLE",
            "reason": "empty_input",
            "authority": dict(AUTHORITY),
        }

    nodes: List[Dict[str, Any]] = []
    lifecycle_state = str(raw_lifecycle_state or "stable")
    state_color = STATE_TOKEN_MAP.get(lifecycle_state, "stable")
    nodes.append({
        "source_key": "lifecycle_state",
        "type": "state",
        "weight": 1.0,
        "color_token": state_color,
    })
    for alert in alerts:
        sev = str(alert.get("severity") or "warning")
        color = "critical" if sev == "critical" else "warning"
        nodes.append({
            "source_key": str(alert.get("message") or "alert"),
            "type": "alert",
            "weight": 0.8,
            "color_token": color,
        })
    for action in actions:
        pri = str(action.get("priority") or "warning")
        color = "critical" if pri == "high" else "warning"
        nodes.append({
            "source_key": str(action.get("label") or action.get("action") or "action"),
            "type": "action",
            "weight": 0.6,
            "color_token": color,
        })

    layout = default_layout(len(nodes))
    grid_width = int(layout["grid_width"])
    spacing = float(layout["spacing"])

    materialized_nodes: List[Dict[str, Any]] = []
    for i, node in enumerate(nodes):
        nid = _node_id(node["source_key"], node["type"], i)
        materialized_nodes.append({
            "id": nid,
            "source_key": node["source_key"],
            "position": _position(i, grid_width, spacing),
            "type": node["type"],
            "weight": float(node["weight"]),
            "color_token": node["color_token"],
        })

    alert_nodes = [n for n in materialized_nodes if n["type"] == "alert"]
    action_nodes = [n for n in materialized_nodes if n["type"] == "action"]
    state_node = materialized_nodes[0] if materialized_nodes else None

    edges: List[Dict[str, Any]] = []
    if state_node is not None:
        for n in alert_nodes:
            edges.append({"source": state_node["id"], "target": n["id"], "type": "dependency"})
    for an in alert_nodes:
        for ac in action_nodes:
            edges.append({"source": an["id"], "target": ac["id"], "type": "flow"})

    materialized_edges = [{**e, "id": _edge_id(e["source"], e["target"])} for e in edges]
    materialized_edges.sort(key=lambda e: (e["source"], e["target"], e["id"]))

    scene_core = {"nodes": materialized_nodes, "edges": materialized_edges}
    scene_id = sha256_hex(canonical_json(scene_core))
    view_packet_hash = sha256_hex(canonical_json(packet))

    spec = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "authority": dict(AUTHORITY),
        "scene": {"scene_id": scene_id, "node_count": len(materialized_nodes), "edge_count": len(materialized_edges)},
        "camera": {"type": "orthographic", "position": [0, 0, 100], "target": [0, 0, 0], "zoom": 1.0},
        "layout": layout,
        "nodes": materialized_nodes,
        "edges": materialized_edges,
        "alert_layers": [n for n in materialized_nodes if n["type"] == "alert"],
        "action_vectors": [e for e in materialized_edges if e["type"] == "flow"],
        "materials": MATERIALS,
        "animation_intent": {"description": "static_scene_no_runtime"},
        "performance_budget": {"max_nodes": 2048, "max_edges": 8192},
        "lineage": {"view_packet_hash": view_packet_hash, "scene_hash": ""},
    }
    scene_hash = sha256_hex(canonical_json(spec))
    spec["lineage"]["scene_hash"] = scene_hash
    return spec
