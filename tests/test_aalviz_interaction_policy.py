from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.interaction_policy import build_interaction_policy
from abraxas.viz.interaction_policy_runner import run_interaction_policy


def _viewer_spec():
    return {"artifact": "AAL-VIZ-WEBGL-STATIC-VIEWER-001", "schema_version": "AALVizWebGLStaticViewerSpec.v1", "viewer_id": "a" * 64}


def _component_manifest():
    return {"artifact": "AAL-VIZ-WEBGL-REACT-COMPONENT-001", "schema_version": "AALVizReactComponentManifest.v1", "manifest_id": "b" * 64}


def test_interaction_policy_deterministic_and_flags(tmp_path: Path):
    v = _viewer_spec()
    c = _component_manifest()
    v_before = deepcopy(v)
    c_before = deepcopy(c)

    p1 = build_interaction_policy(v, c)
    p2 = build_interaction_policy(v, c)
    assert canonical_json(p1) == canonical_json(p2)
    assert p1["policy_id"] == p2["policy_id"]
    assert p1["policy_hash"] == p2["policy_hash"]

    pcopy = deepcopy(p1)
    pcopy["policy_hash"] = ""
    assert p1["policy_hash"] == sha256_hex(canonical_json(pcopy))

    assert not set(p1["allowed_future_interactions"]).intersection(set(p1["forbidden_interactions"]))
    assert p1["event_policy"]["event_binding_allowed"] is False
    assert p1["mutation_policy"]["runtime_mutation_allowed"] is False

    auth = p1["authority"]
    assert auth["interaction_policy_generation"] is True
    for key in ("interaction_runtime", "event_listener_binding", "animation_runtime", "request_animation_frame", "physics_simulation", "browser_runtime_mutation", "inference", "production_activation", "baseline_mutation", "runtime_config_write", "promotion", "execution", "scheduler"):
        assert auth[key] is False

    assert v == v_before
    assert c == c_before

    v_path = tmp_path / "viewer.json"
    c_path = tmp_path / "component.json"
    out_path = tmp_path / "policy.json"
    v_path.write_text(canonical_json(v), encoding="utf-8")
    c_path.write_text(canonical_json(c), encoding="utf-8")
    run_interaction_policy(v_path, c_path, out_path)
    first = out_path.read_bytes()
    run_interaction_policy(v_path, c_path, out_path)
    assert first == out_path.read_bytes()
