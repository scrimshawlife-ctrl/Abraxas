from __future__ import annotations

from webpanel.burst_dry_run import simulate_burst
from webpanel.core_bridge import core_ingest
from webpanel.models import AbraxasSignalPacket, RunState
from webpanel.runplan import build_runplan


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
    run = RunState(**result)
    run.runplan = build_runplan(run)
    return run


def test_effective_n_respects_session_remaining_and_cap():
    run = _run("sig-burst")
    run.session_active = True
    run.session_max_steps = 3
    run.session_steps_used = 0
    run.agency_enabled = True
    run.agency_mode = "burst"

    preview = simulate_burst(run, 5)

    assert preview["effective_n"] == 3
    assert preview["requested_n"] == 5
    assert preview["provenance"]["session_remaining"] == 3
    assert len(preview["steps"]) == 3


def test_policy_mismatch_adds_blocker():
    run = _run("sig-policy")
    run.policy_hash_at_ingest = "hash_mismatch"
    run.policy_ack = False
    run.session_active = True
    run.session_max_steps = 3
    run.agency_enabled = True
    run.agency_mode = "burst"

    preview = simulate_burst(run, 2)

    assert "policy_ack_required" in preview["blockers"]


def test_simulation_does_not_mutate_run_state():
    run = _run("sig-mutation")
    run.session_active = True
    run.session_max_steps = 2
    run.session_steps_used = 0
    run.agency_enabled = True
    run.agency_mode = "burst"

    before_index = run.current_step_index
    before_steps_used = run.session_steps_used
    before_runplan_hash = run.runplan.deterministic_hash

    _ = simulate_burst(run, 1)

    assert run.current_step_index == before_index
    assert run.session_steps_used == before_steps_used
    assert run.runplan.deterministic_hash == before_runplan_hash
