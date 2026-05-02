import json
from pathlib import Path

import pytest

from abraxas.proof.proof_state_viz_adapter import build_projection, canonical_json


def _write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_deterministic_output_and_propagation(tmp_path: Path):
    reg = tmp_path / "out/proof/proof_registry.latest.json"
    _write(reg, {
        "combined_status": "LOCAL_CHAIN_PROVEN",
        "pointer_closure": "PASS",
        "drift_class": "repo_ahead",
        "repo_proof": {"x": 1},
        "runtime_proof": {"y": 2},
    })
    p1 = build_projection(reg)
    p2 = build_projection(reg)
    assert canonical_json(p1) == canonical_json(p2)
    assert p1["combined_status"] == "LOCAL_CHAIN_PROVEN"
    assert p1["pointer_closure"] == "PASS"
    assert p1["drift_class"] == "repo_ahead"


def test_fail_closed_missing_registry(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        build_projection(tmp_path / "missing.json")


def test_authority_flags_enforced(tmp_path: Path):
    reg = tmp_path / "out/proof/proof_registry.latest.json"
    _write(reg, {
        "combined_status": "LOCAL_CHAIN_PROVEN",
        "pointer_closure": "PASS",
        "drift_class": "repo_ahead",
        "repo_proof": {"x": 1},
        "runtime_proof": {"y": 2},
    })
    p = build_projection(reg)
    assert p["authority"]["projection_only"] is True
    assert p["authority"]["promotion_allowed"] is False
    assert p["authority"]["runtime_mutation"] is False
    assert p["authority"]["forecast_influence"] is False
