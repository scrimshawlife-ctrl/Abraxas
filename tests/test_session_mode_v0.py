from __future__ import annotations

import pytest

from webpanel.core_bridge import core_ingest
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, RunState
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


def test_session_mode_flow():
    run = _run("sig-session")
    ledger = LedgerChain()

    with pytest.raises(SessionGateError) as exc:
        enforce_session(run)
    assert exc.value.reason == "session_required"

    start_session(
        run=run,
        max_steps=3,
        started_utc="2026-02-03T00:00:00+00:00",
        ledger=ledger,
        event_id="ev_start",
    )
    assert run.session_active is True
    assert run.session_max_steps == 3
    assert run.session_steps_used == 0

    for idx in range(3):
        enforce_session(run)
        consume_session_step(
            run=run,
            ledger=ledger,
            event_id=f"ev_step_{idx}",
            end_event_id=f"ev_end_{idx}",
            timestamp_utc=f"2026-02-03T00:00:0{idx}+00:00",
            route="defer_step:runplan",
            step_index=idx,
        )

    assert run.session_steps_used == 3
    assert run.session_active is False

    with pytest.raises(SessionGateError) as exc:
        enforce_session(run)
    assert exc.value.reason == "session_exhausted"

    start_session(
        run=run,
        max_steps=2,
        started_utc="2026-02-03T00:00:10+00:00",
        ledger=ledger,
        event_id="ev_start_2",
    )
    end_session(
        run=run,
        ended_utc="2026-02-03T00:00:11+00:00",
        ledger=ledger,
        event_id="ev_end_user",
        reason="user",
    )
    assert run.session_active is False

    events = ledger.list_events(run.run_id)
    types = [event.event_type for event in events]
    assert "session_start" in types
    assert "session_step" in types
    assert "session_end" in types
