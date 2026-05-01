from __future__ import annotations

from copy import deepcopy

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.webgl_static_viewer import build_static_viewer_spec


def _bundle():
    return {
        "artifact": "AAL-VIZ-WEBGL-RENDERER-SCAFFOLD-001",
        "schema_version": "AALVizWebGLRenderBundle.v1",
        "buffers": {
            "positions": [0.0, 0.0, 0.0, 10.0, 0.0, 0.0],
            "colors": [0.0, 1.0, 0.78, 1.0, 0.72, 0.0],
            "indices": [0, 1],
        },
        "draw_calls": [{"mode": "POINTS", "count": 2, "offset": 0}, {"mode": "LINES", "count": 2, "offset": 0}],
        "camera_uniforms": {"position": [0, 0, 100], "target": [0, 0, 0], "zoom": 1.0},
        "material_uniforms": {"color_palette": {"stable": "#00FFC6"}},
        "scene_summary": {"node_count": 2, "edge_count": 1},
    }


def test_static_viewer_spec_generation_and_determinism():
    bundle = _bundle()
    before = deepcopy(bundle)
    s1 = build_static_viewer_spec(bundle)
    s2 = build_static_viewer_spec(bundle)

    assert s1["component_contract"]["required_props"] == ["renderBundle", "width", "height"]
    assert s1["viewer"]["supports_interaction"] is False
    assert s1["viewer"]["supports_animation"] is False
    assert all(v is False for v in s1["interaction_policy"].values())
    assert s1["draw_plan"]["draw_calls"] == bundle["draw_calls"]
    assert s1["camera_defaults"] == bundle["camera_uniforms"]
    assert s1["material_defaults"] == bundle["material_uniforms"]
    assert s1["diagnostics"]["positions_length"] == len(bundle["buffers"]["positions"])
    assert s1["diagnostics"]["colors_length"] == len(bundle["buffers"]["colors"])
    assert s1["diagnostics"]["indices_length"] == len(bundle["buffers"]["indices"])
    assert s1["viewer_id"] == s2["viewer_id"]
    assert s1["lineage"]["viewer_spec_hash"] == s2["lineage"]["viewer_spec_hash"]
    assert canonical_json(s1) == canonical_json(s2)
    assert bundle == before

    vcopy = deepcopy(s1)
    vcopy["lineage"]["viewer_spec_hash"] = ""
    assert s1["lineage"]["viewer_spec_hash"] == sha256_hex(canonical_json(vcopy))


def test_empty_bundle_behavior_and_authority():
    spec = build_static_viewer_spec({})
    assert spec["draw_plan"]["draw_calls"] == []
    assert spec["diagnostics"] == {"node_count": 0, "edge_count": 0, "positions_length": 0, "colors_length": 0, "indices_length": 0}
    assert spec["viewer"]["runtime_mode"] == "static_no_loop"

    auth = spec["authority"]
    assert auth["static_viewer_spec_generation"] is True
    for key in ("webgl_rendering", "animation_runtime", "physics_simulation", "browser_runtime_mutation", "inference", "production_activation", "baseline_mutation", "runtime_config_write", "promotion", "execution", "scheduler"):
        assert auth[key] is False
