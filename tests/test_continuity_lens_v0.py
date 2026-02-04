from __future__ import annotations

from webpanel.continuity import build_continuity_report, stable_hash
from webpanel.core_bridge import core_ingest
from webpanel.gates import compute_gate_stack
from webpanel.ledger import LedgerChain
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


def _oracle_output(flags: dict, input_hash: str, policy_hash: str) -> dict:
    return {
        "signal_id": "sig-oracle",
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {"score": 0.5},
        "evidence": [],
        "flags": flags,
        "provenance": {
            "input_hash": input_hash,
            "policy_hash": policy_hash,
            "operator_versions": {},
            "stability_status": {"passed": True, "drift_class": "nondeterminism"},
        },
    }


def test_continuity_report_deterministic_and_capped():
    prev = _run("sig-prev")
    current = _run("sig-current")
    current.prev_run_id = prev.run_id

    prev.oracle_output = _oracle_output({"flag_a": True}, "hash_a", "policy_a")
    current.oracle_output = _oracle_output({"flag_b": True}, "hash_b", "policy_b")

    prev.policy_hash_at_ingest = "policy_a"
    current.policy_hash_at_ingest = "policy_a"
    current.policy_ack = False

    ledger = LedgerChain()
    ledger.append(prev.run_id, "ev_prev", "packet_received", "2026-02-03T00:00:00+00:00", {})
    ledger.append(current.run_id, "ev_curr", "packet_received", "2026-02-03T00:00:01+00:00", {})
    ledger.append(current.run_id, "ev_curr2", "context_created", "2026-02-03T00:00:02+00:00", {})

    setattr(prev, "ledger_events", ledger.list_events(prev.run_id))
    setattr(current, "ledger_events", ledger.list_events(current.run_id))
    report_a = build_continuity_report(current, prev, "policy_b")
    report_b = build_continuity_report(current, prev, "policy_b")

    assert stable_hash(report_a) == stable_hash(report_b)
    assert len(report_a["summary_lines"]) <= 7
    assert len(report_a["risk_notes"]) <= 7
    assert "oracle" in report_a["deltas"]
    assert report_a["deltas"]["oracle"]["flags_added"]
    top_code = compute_gate_stack(current, "policy_b")[0]["code"]
    assert report_a["deltas"]["gates"]["top_gate_now"] == top_code
