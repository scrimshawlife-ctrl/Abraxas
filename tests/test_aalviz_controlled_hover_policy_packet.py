from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.controlled_hover_packet import build_packet
from abraxas.viz.controlled_hover_runner import run


def _inputs(frontend_execution: str = "not_computable_environment", ledger_status: str = "review_ready", allow_hover: bool = True):
    policy = {"policy_hash": "p" * 64, "allowed_future_interactions": ["node_hover"] if allow_hover else ["edge_highlight"]}
    ledger = {"entries": [{"entry_id": "1", "promotion_status": {"status": ledger_status}}]}
    prov = {"manifest_hash": "v" * 64}
    ci = {"proof_hash": "c" * 64, "frontend_execution": frontend_execution}
    comp = {"artifact": "AAL-VIZ-WEBGL-REACT-COMPONENT-001", "schema_version": "AALVizReactComponentManifest.v1", "manifest_hash": "m" * 64}
    return policy, ledger, prov, ci, comp


def test_blocked_when_frontend_not_verified():
    p = build_packet(*_inputs(frontend_execution="not_computable_environment"))
    assert p["status"]["value"] == "blocked"
    assert p["status"]["reason"] == "frontend_execution_not_verified"


def test_review_ready_when_verified_and_ledger_ready():
    p = build_packet(*_inputs(frontend_execution="verified", ledger_status="review_ready", allow_hover=True))
    assert p["status"]["value"] == "review_ready"
    assert p["status"]["blockers"] == []


def test_missing_node_hover_blocks():
    p = build_packet(*_inputs(frontend_execution="verified", ledger_status="review_ready", allow_hover=False))
    assert p["status"]["reason"] == "node_hover_not_allowed_by_policy"


def test_determinism_and_hash_and_runtime_lock(tmp_path: Path):
    inputs = _inputs(frontend_execution="verified", ledger_status="review_ready", allow_hover=True)
    before = deepcopy(inputs)
    p1 = build_packet(*inputs)
    p2 = build_packet(*inputs)
    assert p1["packet_id"] == p2["packet_id"]
    assert p1["packet_hash"] == p2["packet_hash"]
    assert "requestAnimationFrame" in p1["hover_contract"]["forbidden_runtime_apis"]
    assert "pointermove" in p1["hover_contract"]["forbidden_runtime_bindings"]
    assert p1["readiness"]["runtime_authority_locked"] is True
    tmp = deepcopy(p1)
    tmp["packet_hash"] = ""
    assert p1["packet_hash"] == sha256_hex(canonical_json(tmp))
    assert inputs == before

    ip, pl, pm, cp, cm = inputs
    pp = tmp_path / "ip.json"; lp = tmp_path / "pl.json"; vp = tmp_path / "pm.json"; cp2 = tmp_path / "cp.json"; cm2 = tmp_path / "cm.json"; out = tmp_path / "out.json"
    pp.write_text(canonical_json(ip)); lp.write_text(canonical_json(pl)); vp.write_text(canonical_json(pm)); cp2.write_text(canonical_json(cp)); cm2.write_text(canonical_json(cm))
    run(pp, lp, vp, cp2, cm2, out)
    first = out.read_bytes()
    run(pp, lp, vp, cp2, cm2, out)
    assert first == out.read_bytes()


def test_malformed_input_not_computable():
    policy, ledger, prov, ci, comp = _inputs()
    del policy["policy_hash"]
    p = build_packet(policy, ledger, prov, ci, comp)
    assert p["status"]["value"] == "not_computable"
