from __future__ import annotations

from webpanel.consideration import build_consideration, stable_hash
from webpanel.core_bridge import core_ingest
from webpanel.gates import compute_gate_stack
from webpanel.models import AbraxasSignalPacket, RunState


def _packet(signal_id: str) -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id=signal_id,
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={"alpha": {"beta": 1}},
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def _run(signal_id: str) -> RunState:
    result = core_ingest(_packet(signal_id).model_dump())
    return RunState(**result)


def _oracle_output() -> dict:
    return {
        "signal_id": "sig-oracle",
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {"score": 0.9, "status": "ok"},
        "evidence": ["ref-a", {"id": "ref-b"}],
        "flags": {"evidence_missing": True},
        "provenance": {
            "input_hash": "inputhash",
            "policy_hash": "policyhash",
            "operator_versions": {"extract_structure_v0": "v0"},
            "stability_status": {"passed": True, "drift_class": "nondeterminism"},
        },
    }


def test_consideration_deterministic_and_bounded():
    run = _run("sig-consider")
    oracle = _oracle_output()
    run.oracle_output = oracle
    run.session_active = True
    gates = compute_gate_stack(run, "policyhash")
    proposal = {
        "action_id": "act_test",
        "kind": "request_missing_integrity",
        "title": "Request missing integrity evidence",
        "rationale": ["reason-a", "reason-b"],
        "required_gates": ["ack_required"],
        "expected_entropy_reduction": 0.5,
        "risk_notes": "low risk",
    }

    consideration_a = build_consideration(run, proposal, oracle, gates)
    consideration_b = build_consideration(run, proposal, oracle, gates)
    assert stable_hash(consideration_a) == stable_hash(consideration_b)
    assert len(consideration_a["rationale"]) <= 7
    assert len(consideration_a["dependencies"]) <= 10
    assert len(consideration_a["counterfactuals"]) <= 5
    assert len(consideration_a["risk_flags"]) <= 10
    assert len(consideration_a["evidence_refs"]) <= 20
    assert "drift_blocked" in consideration_a["provenance"]["gate_codes"]
    assert any(line.startswith("oracle.indicator") for line in consideration_a["rationale"])
