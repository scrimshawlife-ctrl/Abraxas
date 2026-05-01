from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.react_component_manifest import SOURCE_PATHS, build_manifest
from abraxas.viz.react_component_manifest_runner import run_manifest


def test_manifest_generation_and_determinism_and_source_scan(tmp_path: Path):
    repo_root = Path('.')
    m1 = build_manifest(repo_root)
    m2 = build_manifest(repo_root)

    assert m1["artifact"] == "AAL-VIZ-WEBGL-REACT-COMPONENT-001"
    assert [x["path"] for x in m1["source_files"]] == SOURCE_PATHS
    assert m1["source_files"] == m2["source_files"]
    assert m1["manifest_id"] == m2["manifest_id"]

    c = deepcopy(m1)
    c["manifest_hash"] = ""
    assert m1["manifest_hash"] == sha256_hex(canonical_json(c))

    assert m1["component"]["mode"] == "static_single_frame"
    auth = m1["authority"]
    assert auth["react_component_scaffold_generation"] is True
    assert auth["static_single_frame_render"] is True
    for key in ("animation_runtime", "request_animation_frame", "physics_simulation", "browser_runtime_mutation", "inference", "production_activation", "baseline_mutation", "runtime_config_write", "promotion", "execution", "scheduler"):
        assert auth[key] is False

    component_src = (repo_root / SOURCE_PATHS[1]).read_text(encoding='utf-8')
    for forbidden in ("requestAnimationFrame", "setInterval", "setTimeout", "Math.random", "Date.now"):
        assert forbidden not in component_src

    out = tmp_path / 'manifest.json'
    run_manifest(repo_root, out)
    first = out.read_bytes()
    run_manifest(repo_root, out)
    assert first == out.read_bytes()
