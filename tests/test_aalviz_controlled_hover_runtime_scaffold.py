from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.controlled_hover_scaffold import build_scaffold
from abraxas.viz.controlled_hover_scaffold_runner import run


def _inputs(packet_status: str = "review_ready", fe: str = "verified"):
    hp = {"status": {"value": packet_status}}
    cp = {"frontend_execution": fe}
    cm = {"manifest_hash": "m" * 64}
    return hp, cp, cm


def test_blocked_when_ci_not_verified():
    s = build_scaffold(*_inputs(packet_status="review_ready", fe="not_computable_environment"))
    assert s["status"]["reason"] == "frontend_execution_not_verified"


def test_blocked_when_hover_packet_not_ready():
    s = build_scaffold(*_inputs(packet_status="blocked", fe="verified"))
    assert s["status"]["reason"] == "hover_packet_not_review_ready"


def test_review_ready_only_when_both_gates_pass():
    s = build_scaffold(*_inputs(packet_status="review_ready", fe="verified"))
    assert s["status"]["value"] == "review_ready"


def test_determinism_and_no_runtime_enablement_and_no_mutation(tmp_path: Path):
    hp, cp, cm = _inputs(packet_status="review_ready", fe="verified")
    before = (deepcopy(hp), deepcopy(cp), deepcopy(cm))
    s1 = build_scaffold(hp, cp, cm)
    s2 = build_scaffold(hp, cp, cm)
    assert s1["diff_preview"] == s2["diff_preview"]
    assert s1["scaffold_id"] == s2["scaffold_id"]
    assert s1["authority"]["runtime_enabled"] is False
    tmp = deepcopy(s1)
    tmp["scaffold_hash"] = ""
    assert s1["scaffold_hash"] == sha256_hex(canonical_json(tmp))
    assert (hp, cp, cm) == before

    p1 = tmp_path / "hp.json"; p2 = tmp_path / "cp.json"; p3 = tmp_path / "cm.json"; o = tmp_path / "o.json"
    p1.write_text(canonical_json(hp)); p2.write_text(canonical_json(cp)); p3.write_text(canonical_json(cm))
    run(p1, p2, p3, o)
    first = o.read_bytes()
    run(p1, p2, p3, o)
    assert first == o.read_bytes()
