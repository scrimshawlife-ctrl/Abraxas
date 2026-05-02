import json
from pathlib import Path

import pytest

from abraxas.operator.canary_readiness import build_canary_readiness, canonical_json


def _write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _card(health="GREEN", pointer="PASS", mode="OBSERVE_ONLY"):
    return {
        "schema": "ProofStatusCard.v1",
        "status": "LOCAL_CHAIN_PROVEN",
        "health": health,
        "pointer_closure": pointer,
        "authority": {"mode": mode},
    }


def test_readiness_true_case(tmp_path: Path):
    p = tmp_path / "card.json"
    _write(p, _card())
    r = build_canary_readiness(p)
    assert r["canary_ready"] is True
    assert r["blocked"] is False
    assert r["blockers"] == []


def test_readiness_false_cases_and_determinism(tmp_path: Path):
    p = tmp_path / "card.json"
    _write(p, _card(health="YELLOW", pointer="FAIL", mode="ACTIVE"))
    r1 = build_canary_readiness(p)
    r2 = build_canary_readiness(p)
    assert canonical_json(r1) == canonical_json(r2)
    assert r1["canary_ready"] is False
    assert r1["blocked"] is True
    assert set(r1["blockers"]) == {"HEALTH_NOT_GREEN", "POINTER_CLOSURE_NOT_PASS", "AUTHORITY_MODE_INVALID"}


def test_fail_closed_behavior(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        build_canary_readiness(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    _write(bad, {"schema": "x"})
    with pytest.raises(ValueError):
        build_canary_readiness(bad)


def test_authority_flags_enforced(tmp_path: Path):
    p = tmp_path / "card.json"
    _write(p, _card())
    r = build_canary_readiness(p)
    assert r["authority"]["can_activate_canary"] is False
    assert r["authority"]["can_mutate_runtime"] is False
    assert r["authority"]["mode"] == "READINESS_ONLY"
