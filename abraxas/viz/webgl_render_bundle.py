from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.webgl_render_models import ARTIFACT, AUTHORITY, COLOR_MAP, SCHEMA_VERSION
from abraxas.viz.webgl_render_validator import validate_authority, validate_no_nan, validate_scene


def build_render_bundle(scene_spec: Dict[str, Any]) -> Dict[str, Any]:
    validate_authority()
    validate_scene(scene_spec)
    scene_in = deepcopy(scene_spec)

    nodes = list(scene_in.get("nodes") or [])
    edges = list(scene_in.get("edges") or [])
    if not nodes:
        return {
            "artifact": ARTIFACT,
            "schema_version": SCHEMA_VERSION,
            "status": "NOT_COMPUTABLE",
            "reason": "empty_scene",
            "authority": dict(AUTHORITY),
        }

    nodes_sorted = sorted(nodes, key=lambda n: str(n.get("id", "")))
    edges_sorted = sorted(edges, key=lambda e: str(e.get("id", "")))

    id_to_index = {str(n["id"]): i for i, n in enumerate(nodes_sorted)}

    positions: List[float] = []
    colors: List[float] = []
    for n in nodes_sorted:
        pos = list(n.get("position") or [0.0, 0.0])
        positions.extend([float(pos[0]), float(pos[1]), 0.0])
        colors.extend(COLOR_MAP.get(str(n.get("color_token", "stable")), COLOR_MAP["stable"]))

    indices: List[int] = []
    for e in edges_sorted:
        s = id_to_index.get(str(e.get("source")), 0)
        t = id_to_index.get(str(e.get("target")), 0)
        indices.extend([int(s), int(t)])

    validate_no_nan(positions)
    validate_no_nan(colors)

    bundle = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "authority": dict(AUTHORITY),
        "buffers": {"positions": positions, "colors": colors, "indices": indices},
        "draw_calls": [
            {"mode": "POINTS", "count": len(nodes_sorted), "offset": 0},
            {"mode": "LINES", "count": len(indices), "offset": 0},
        ],
        "camera_uniforms": deepcopy(scene_in.get("camera") or {"position": [0, 0, 100], "target": [0, 0, 0], "zoom": 1.0}),
        "material_uniforms": {"color_palette": deepcopy(scene_in.get("materials", {}).get("color_tokens", COLOR_MAP))},
        "scene_summary": {"node_count": len(nodes_sorted), "edge_count": len(edges_sorted)},
        "performance_budget": deepcopy(scene_in.get("performance_budget") or {"max_nodes": 0, "max_edges": 0}),
        "lineage": {"scene_spec_hash": sha256_hex(canonical_json(scene_in)), "render_bundle_hash": ""},
    }

    bundle_hash = sha256_hex(canonical_json(bundle))
    bundle["lineage"]["render_bundle_hash"] = bundle_hash

    if len(positions) != len(nodes_sorted) * 3:
        raise ValueError("positions length mismatch")
    if len(colors) != len(nodes_sorted) * 3:
        raise ValueError("colors length mismatch")
    if len(indices) != len(edges_sorted) * 2:
        raise ValueError("indices length mismatch")
    return bundle
