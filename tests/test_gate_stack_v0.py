from __future__ import annotations

from jinja2 import Environment, FileSystemLoader

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


def _oracle_output(drift_class: str) -> dict:
    return {
        "signal_id": "sig-oracle",
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {},
        "evidence": [],
        "flags": {},
        "provenance": {
            "input_hash": "input",
            "policy_hash": "policy",
            "operator_versions": {},
            "stability_status": {"passed": True, "drift_class": drift_class},
        },
    }


def test_gate_priority_policy_over_session():
    run = _run("sig-policy")
    run.policy_hash_at_ingest = "hash_a"
    run.policy_ack = False
    run.session_active = False
    gates = compute_gate_stack(run, "hash_b")
    assert gates[0]["code"] == "policy_ack_required"


def test_gate_priority_session_exhausted():
    run = _run("sig-session")
    run.policy_hash_at_ingest = "hash_a"
    run.policy_ack = True
    run.session_max_steps = 2
    run.session_steps_used = 2
    gates = compute_gate_stack(run, "hash_a")
    assert gates[0]["code"] == "session_exhausted"


def test_gate_priority_drift_blocked():
    run = _run("sig-drift")
    run.policy_hash_at_ingest = "hash_a"
    run.policy_ack = True
    run.session_active = True
    run.session_max_steps = 3
    run.session_steps_used = 1
    run.oracle_output = _oracle_output("nondeterminism")
    gates = compute_gate_stack(run, "hash_a")
    assert gates[0]["code"] == "drift_blocked"


def test_gate_priority_quota_exhausted():
    run = _run("sig-quota")
    run.policy_hash_at_ingest = "hash_a"
    run.policy_ack = True
    run.session_active = True
    run.session_max_steps = 3
    run.session_steps_used = 0
    run.deferral_active = True
    run.quota_max_actions = 1
    run.actions_taken = 1
    gates = compute_gate_stack(run, "hash_a")
    assert gates[0]["code"] == "quota_exhausted"


def test_banner_rendered_on_run_page():
    run = _run("sig-banner")
    run.policy_hash_at_ingest = "hash_a"
    run.policy_ack = False
    gates = compute_gate_stack(run, "hash_b")
    env = Environment(loader=FileSystemLoader("webpanel/templates"), autoescape=True)
    template = env.get_template("run.html")
    rendered = template.render(
        run=run,
        events=[],
        chain_valid=True,
        lineage_ids=[],
        panel_token="",
        panel_host="",
        panel_port="",
        token_enabled=False,
        current_policy_hash="hash_b",
        current_policy_snapshot={},
        policy_status="CHANGED",
        policy_diff_keys=[],
        policy_ack_required=True,
        policy_current_hash="hash_b",
        oracle_view=None,
        oracle_validation={"valid": True, "errors": []},
        gate_stack=gates,
        top_gate=gates[0],
    )
    assert "Gate:" in rendered
    assert "Policy changed since ingest." in rendered
