import json
from pathlib import Path

import pytest

from abraxas.operator.proof_status_card import build_status_card, canonical_json


def _write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _projection(status="LOCAL_CHAIN_PROVEN", closure="PASS"):
    return {
        "schema": "ProofStateProjection.v1",
        "combined_status": status,
        "pointer_closure": closure,
        "drift_class": "repo_ahead",
        "proof_layers": {"repo": "PRESENT", "runtime": "PRESENT", "registry": "BOUND"},
        "authority": {"projection_only": True, "promotion_allowed": False, "runtime_mutation": False, "forecast_influence": False},
    }


def test_deterministic_output_and_layer_mapping(tmp_path: Path):
    p = tmp_path / "in.json"
    _write(p, _projection())
    c1 = build_status_card(p)
    c2 = build_status_card(p)
    assert canonical_json(c1) == canonical_json(c2)
    assert c1["layers"] == {"repo": "OK", "runtime": "OK", "registry": "OK", "projection": "OK"}


def test_health_calculation():
    assert build_status_card_from_obj(_projection())["health"] == "GREEN"
    assert build_status_card_from_obj(_projection("NOT_COMPUTABLE", "PASS"))["health"] == "YELLOW"
    assert build_status_card_from_obj(_projection("LOCAL_CHAIN_PROVEN", "FAIL"))["health"] == "RED"


def build_status_card_from_obj(data: dict):
    p = Path("/tmp/proj_test.json")
    p.write_text(json.dumps(data), encoding="utf-8")
    try:
        return build_status_card(p)
    finally:
        p.unlink(missing_ok=True)


def test_fail_closed_behavior(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        build_status_card(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    _write(bad, {"schema": "x"})
    with pytest.raises(ValueError):
        build_status_card(bad)


def test_authority_flags_enforced(tmp_path: Path):
    p = tmp_path / "in.json"
    _write(p, _projection())
    c = build_status_card(p)
    assert c["authority"]["can_promote"] is False
    assert c["authority"]["can_mutate_runtime"] is False
    assert c["authority"]["can_influence_forecast"] is False
    assert c["authority"]["mode"] == "OBSERVE_ONLY"
