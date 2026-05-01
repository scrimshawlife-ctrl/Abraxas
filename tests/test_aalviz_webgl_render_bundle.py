from __future__ import annotations

from copy import deepcopy

from abraxas.core.canonical import canonical_json
from abraxas.viz.webgl_render_bundle import build_render_bundle


def _scene_spec():
    return {
        "artifact": "AAL-VIZ-WEBGL-SCENE-SPEC-001",
        "schema_version": "AALVizWebGLSceneSpec.v1",
        "authority": {},
        "camera": {"position": [0, 0, 100], "target": [0, 0, 0], "zoom": 1.0},
        "materials": {"color_tokens": {"stable": "#00FFC6", "warning": "#FFB800", "critical": "#FF3B3B"}},
        "performance_budget": {"max_nodes": 2048, "max_edges": 8192},
        "nodes": [
            {"id": "b", "position": [10.0, 0.0], "color_token": "warning"},
            {"id": "a", "position": [0.0, 0.0], "color_token": "stable"},
        ],
        "edges": [{"id": "e2", "source": "b", "target": "a"}, {"id": "e1", "source": "a", "target": "b"}],
    }


def test_bundle_generation_and_determinism_and_draw_calls():
    spec = _scene_spec()
    before = deepcopy(spec)
    b1 = build_render_bundle(spec)
    b2 = build_render_bundle(spec)

    assert b1["buffers"]["positions"] == [0.0, 0.0, 0.0, 10.0, 0.0, 0.0]
    assert b1["buffers"]["colors"] == [0.0, 1.0, 0.78, 1.0, 0.72, 0.0]
    assert b1["buffers"]["indices"] == [0, 1, 1, 0]
    assert b1["draw_calls"][0]["mode"] == "POINTS"
    assert b1["draw_calls"][1]["mode"] == "LINES"
    assert b1["lineage"]["scene_spec_hash"] == b2["lineage"]["scene_spec_hash"]
    assert b1["lineage"]["render_bundle_hash"] == b2["lineage"]["render_bundle_hash"]
    assert canonical_json(b1) == canonical_json(b2)
    assert spec == before

    auth = b1["authority"]
    assert auth["webgl_render_bundle_generation"] is True
    for key in ("webgl_rendering", "animation_runtime", "physics_simulation", "browser_runtime", "inference", "production_activation", "baseline_mutation", "runtime_config_write", "promotion", "execution", "scheduler"):
        assert auth[key] is False


def test_empty_scene_not_computable():
    out = build_render_bundle({"nodes": [], "edges": []})
    assert out["status"] == "NOT_COMPUTABLE"
