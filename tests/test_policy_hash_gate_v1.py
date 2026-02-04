from __future__ import annotations

import pytest

from webpanel.core_bridge import core_ingest
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, RunState
from webpanel.policy_gate import PolicyAckRequired, enforce_policy_ack, record_policy_ack


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


def test_policy_gate_blocks_then_allows_after_ack():
    run = _run("sig-gate")
    run.policy_hash_at_ingest = "hash_a"
    current_hash = "hash_b"

    with pytest.raises(PolicyAckRequired):
        enforce_policy_ack(run, current_hash)

    ledger = LedgerChain()
    record_policy_ack(
        run=run,
        current_policy_hash=current_hash,
        ledger=ledger,
        event_id="ev_policy_ack",
        timestamp_utc="2026-02-03T00:00:00+00:00",
    )

    enforce_policy_ack(run, current_hash)

    events = ledger.list_events(run.run_id)
    assert events
    last = events[-1]
    assert last.event_type == "policy_ack"
    assert last.data.get("ingest_policy_hash_prefix") == "hash_a"[:8]
    assert last.data.get("current_policy_hash_prefix") == "hash_b"[:8]
    assert last.data.get("timestamp_utc") == "2026-02-03T00:00:00+00:00"


def test_policy_gate_ignores_missing_ingest_hash():
    run = _run("sig-no-ingest")
    run.policy_hash_at_ingest = None
    enforce_policy_ack(run, "hash_b")


def test_policy_gate_allows_when_hash_matches():
    run = _run("sig-match")
    run.policy_hash_at_ingest = "hash_a"
    enforce_policy_ack(run, "hash_a")
