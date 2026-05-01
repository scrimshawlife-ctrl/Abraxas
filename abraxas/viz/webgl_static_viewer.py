from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.webgl_viewer_models import ARTIFACT, ASSET_BINDINGS, AUTHORITY, COMPONENT_CONTRACT, INTERACTION_POLICY, PROPS_SCHEMA, SCHEMA_VERSION, VIEWER
from abraxas.viz.webgl_viewer_validator import validate_authority, validate_viewer_spec


def _viewer_id_payload(spec: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "artifact": spec["artifact"],
        "schema_version": spec["schema_version"],
        "authority": spec["authority"],
        "viewer": spec["viewer"],
        "component_contract": spec["component_contract"],
        "props_schema": spec["props_schema"],
        "asset_bindings": spec["asset_bindings"],
        "draw_plan": spec["draw_plan"],
        "camera_defaults": spec["camera_defaults"],
        "material_defaults": spec["material_defaults"],
        "interaction_policy": spec["interaction_policy"],
        "diagnostics": spec["diagnostics"],
        "lineage": {"render_bundle_hash": spec["lineage"]["render_bundle_hash"]},
    }


def build_static_viewer_spec(render_bundle: Dict[str, Any]) -> Dict[str, Any]:
    validate_authority()
    bundle = deepcopy(render_bundle)
    bundle_hash = sha256_hex(canonical_json(bundle))

    buffers = bundle.get("buffers") or {}
    positions = list(buffers.get("positions") or [])
    colors = list(buffers.get("colors") or [])
    indices = list(buffers.get("indices") or [])
    has_buffers = len(positions) > 0

    node_count = int((bundle.get("scene_summary") or {}).get("node_count") or 0)
    edge_count = int((bundle.get("scene_summary") or {}).get("edge_count") or 0)

    spec = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "viewer_id": "",
        "authority": dict(AUTHORITY),
        "viewer": dict(VIEWER),
        "component_contract": deepcopy(COMPONENT_CONTRACT),
        "props_schema": deepcopy(PROPS_SCHEMA),
        "asset_bindings": deepcopy(ASSET_BINDINGS),
        "draw_plan": {
            "draw_calls": deepcopy(bundle.get("draw_calls") or []) if has_buffers else [],
            "node_draw_mode": "POINTS",
            "edge_draw_mode": "LINES",
        },
        "camera_defaults": deepcopy(bundle.get("camera_uniforms") or {}),
        "material_defaults": deepcopy(bundle.get("material_uniforms") or {}),
        "interaction_policy": deepcopy(INTERACTION_POLICY),
        "diagnostics": {
            "node_count": node_count,
            "edge_count": edge_count,
            "positions_length": len(positions),
            "colors_length": len(colors),
            "indices_length": len(indices),
        },
        "lineage": {"render_bundle_hash": bundle_hash, "viewer_spec_hash": ""},
    }

    spec["viewer_id"] = sha256_hex(canonical_json(_viewer_id_payload(spec)))
    viewer_hash = sha256_hex(canonical_json(spec))
    spec["lineage"]["viewer_spec_hash"] = viewer_hash

    validate_viewer_spec(spec, bundle)
    return spec
