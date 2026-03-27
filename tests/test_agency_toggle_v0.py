from __future__ import annotations

import pytest

from webpanel.agency_toggle import AgencyGateError, enable_agency, enforce_agency_enabled
from webpanel.core_bridge import core_ingest
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, RunState
from webpanel.policy_gate import PolicyAckRequired, enforce_policy_ack
from webpanel.session_mode import (
    SessionGateError,
    consume_session_step,
    end_session,
    enforce_session,
    start_session,
)


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


def _attempt_enable(run: RunState, current_hash: str, ledger: LedgerChain) -> None:
    enforce_policy_ack(run, current_hash)
    enforce_session(run)
    enable_agency(
        run=run,
        mode="guided",
        timestamp_utc="2026-02-03T00:00:00+00:00",
        ledger=ledger,
        event_id="ev_agency_enable",
        policy_hash=current_hash,
    )


def test_agency_enable_requires_active_session():
    run = _run("sig-agency-session")
    run.policy_hash_at_ingest = "hash_a"
    ledger = LedgerChain()

    with pytest.raises(SessionGateError) as exc:
        _attempt_enable(run, "hash_a", ledger)
    assert exc.value.reason == "session_required"


def test_agency_enable_blocks_on_policy_mismatch_without_ack():
    run = _run("sig-agency-policy")
    run.policy_hash_at_ingest = "hash_a"
    ledger = LedgerChain()
    start_session(
        run=run,
        max_steps=3,
        started_utc="2026-02-03T00:00:00+00:00",
        ledger=ledger,
        event_id="ev_session_start",
    )

    with pytest.raises(PolicyAckRequired):
        _attempt_enable(run, "hash_b", ledger)


def test_agency_enable_succeeds_when_session_active_and_policy_ok():
    run = _run("sig-agency-ok")
    run.policy_hash_at_ingest = "hash_a"
    ledger = LedgerChain()
    start_session(
        run=run,
        max_steps=3,
        started_utc="2026-02-03T00:00:00+00:00",
        ledger=ledger,
        event_id="ev_session_start",
    )

    _attempt_enable(run, "hash_a", ledger)

    assert run.agency_enabled is True
    assert run.agency_mode == "guided"
    events = ledger.list_events(run.run_id)
    assert events[-1].event_type == "agency_enable"


def test_execution_blocked_when_agency_off_allowed_when_on():
    run = _run("sig-agency-gate")
    run.agency_enabled = False

    with pytest.raises(AgencyGateError) as exc:
        enforce_agency_enabled(run)
    assert exc.value.reason == "agency_off"

    run.agency_enabled = True
    run.agency_mode = "guided"
    enforce_agency_enabled(run)


def test_agency_auto_disables_on_session_end_or_exhaustion():
    run = _run("sig-agency-auto")
    run.policy_hash_at_ingest = "hash_a"
    ledger = LedgerChain()
    start_session(
        run=run,
        max_steps=2,
        started_utc="2026-02-03T00:00:00+00:00",
        ledger=ledger,
        event_id="ev_session_start",
    )
    enable_agency(
        run=run,
        mode="guided",
        timestamp_utc="2026-02-03T00:00:01+00:00",
        ledger=ledger,
        event_id="ev_agency_enable",
        policy_hash="hash_a",
    )

    end_session(
        run=run,
        ended_utc="2026-02-03T00:00:02+00:00",
        ledger=ledger,
        event_id="ev_session_end",
        reason="user",
        agency_event_id="ev_agency_disable",
    )
    assert run.agency_enabled is False
    assert run.agency_disable_reason == "session_end"

    start_session(
        run=run,
        max_steps=1,
        started_utc="2026-02-03T00:00:10+00:00",
        ledger=ledger,
        event_id="ev_session_start_2",
    )
    enable_agency(
        run=run,
        mode="guided",
        timestamp_utc="2026-02-03T00:00:11+00:00",
        ledger=ledger,
        event_id="ev_agency_enable_2",
        policy_hash="hash_a",
    )
    consume_session_step(
        run=run,
        ledger=ledger,
        event_id="ev_step",
        end_event_id="ev_end",
        agency_event_id="ev_agency_disable_2",
        timestamp_utc="2026-02-03T00:00:12+00:00",
        route="defer_step:runplan",
        step_index=0,
    )

    assert run.agency_enabled is False
    assert run.agency_disable_reason == "exhausted"
