from __future__ import annotations

from webpanel.core_bridge import core_ingest
from webpanel.models import AbraxasSignalPacket, RunState
from webpanel.task_router import recommend_profile


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


def _oracle_output(drift_class: str, flags: dict | None = None, evidence: list | None = None) -> dict:
    return {
        "signal_id": "sig-oracle",
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {},
        "evidence": evidence or [],
        "flags": flags or {},
        "provenance": {
            "input_hash": "input",
            "policy_hash": "policy",
            "operator_versions": {},
            "stability_status": {"passed": True, "drift_class": drift_class},
        },
    }


def test_rule1_policy_gate_recommends_read_only():
    run = _run("sig-policy")
    run.policy_hash_at_ingest = "hash_a"
    run.policy_ack = False
    run.session_active = True

    rec = recommend_profile(run, None, "hash_b")
    assert rec["recommended_profile_id"] == "read_only_audit"
    assert rec["confidence"] == "high"
    assert rec["reasons"] == ["gate:policy_ack_required"]


def test_rule1_session_inactive_recommends_read_only():
    run = _run("sig-session")
    run.policy_hash_at_ingest = "hash_a"
    run.policy_ack = True
    run.session_active = False

    rec = recommend_profile(run, None, "hash_a")
    assert rec["recommended_profile_id"] == "read_only_audit"
    assert rec["confidence"] == "high"
    assert rec["reasons"] == ["gate:session_inactive"]


def test_rule2_drift_recommends_deep_review():
    run = _run("sig-drift")
    run.policy_hash_at_ingest = "hash_a"
    run.policy_ack = True
    run.session_active = True
    run.oracle_output = _oracle_output("nondeterminism")

    rec = recommend_profile(run, None, "hash_a")
    assert rec["recommended_profile_id"] == "deep_review"
    assert rec["confidence"] == "high"
    assert rec["reasons"] == ["drift:nondeterminism"]


def test_rule3_proposals_with_session_recommends_guided():
    run = _run("sig-proposals")
    run.policy_hash_at_ingest = "hash_a"
    run.policy_ack = True
    run.session_active = True
    run.oracle_output = _oracle_output("none")
    run.last_step_result = {
        "kind": "propose_actions_v0",
        "actions": [{"action_id": "act_1", "kind": "enter_observe_only"}],
    }

    rec = recommend_profile(run, None, "hash_a")
    assert rec["recommended_profile_id"] == "guided_execute_2"
    assert rec["confidence"] == "medium"
    assert rec["reasons"] == ["proposals_available", "session_active"]


def test_rule4_default_read_only_low_confidence():
    run = _run("sig-default")
    run.policy_hash_at_ingest = "hash_a"
    run.policy_ack = True
    run.session_active = True
    run.oracle_output = _oracle_output("none", evidence=["a", "b", "c", "d"])

    rec = recommend_profile(run, None, "hash_a")
    assert rec["recommended_profile_id"] == "read_only_audit"
    assert rec["confidence"] == "low"
    assert rec["reasons"] == ["default"]
    assert len(rec["reasons"]) <= 5
