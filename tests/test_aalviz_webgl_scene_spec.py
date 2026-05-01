from __future__ import annotations

from copy import deepcopy

from abraxas.core.canonical import canonical_json
from abraxas.viz.webgl_scene import build_scene_spec


def _packet():
    return {
        "lifecycle_state": "needs_attention",
        "alerts": [{"severity": "critical", "message": "A1"}],
        "actions": [{"priority": "high", "label": "Fix"}],
    }


def test_scene_spec_deterministic_and_edges_and_authority():
    packet = _packet()
    before = deepcopy(packet)
    s1 = build_scene_spec(packet)
    s2 = build_scene_spec(packet)

    assert s1["artifact"] == "AAL-VIZ-WEBGL-SCENE-SPEC-001"
    assert s1["scene"]["node_count"] == 3
    assert s1["scene"]["edge_count"] == 2
    assert s1["nodes"][0]["position"] == [0.0, 0.0]
    assert s1["nodes"][1]["position"] == [10.0, 0.0]
    assert s1["nodes"][0]["id"] == s2["nodes"][0]["id"]
    assert s1["edges"][0]["id"] == s2["edges"][0]["id"]
    assert canonical_json(s1) == canonical_json(s2)
    assert packet == before

    auth = s1["authority"]
    assert auth["webgl_scene_spec_generation"] is True
    for key in ("webgl_rendering", "animation_runtime", "physics_simulation", "inference", "production_activation", "baseline_mutation", "runtime_config_write", "promotion", "execution", "scheduler"):
        assert auth[key] is False


def test_not_computable_empty_input():
    out = build_scene_spec({})
    assert out["status"] == "NOT_COMPUTABLE"
    assert out["reason"] == "empty_input"
