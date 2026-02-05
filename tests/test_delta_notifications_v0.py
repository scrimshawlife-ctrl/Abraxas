from __future__ import annotations

from webpanel.delta_notifications import compute_delta_notifications
from webpanel.models import AbraxasSignalPacket, DecisionContext, RiskProfile, RunState


def _packet(signal_id: str) -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id=signal_id,
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={"kind": "unit_test"},
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def _context(signal_id: str, risk_notes: str) -> DecisionContext:
    return DecisionContext(
        context_id=f"ctx_{signal_id}",
        source_signal_id=signal_id,
        created_at_utc="2026-02-03T00:00:00+00:00",
        risk_profile=RiskProfile(
            risk_of_action="medium",
            risk_of_inaction="low",
            risk_notes=risk_notes,
        ),
        requires_human_confirmation=False,
        recommended_interaction_mode="advisor",
    )


def _run(run_id: str, signal_id: str, risk_notes: str) -> RunState:
    return RunState(
        run_id=run_id,
        created_at_utc="2026-02-03T00:00:00+00:00",
        phase=3,
        signal=_packet(signal_id),
        context=_context(signal_id, risk_notes),
        requires_human_confirmation=False,
    )


def test_delta_notifications_none_without_prev():
    current = _run("run_current", "sig_current", "notes")
    result = compute_delta_notifications(current, None, "policy_hash")
    assert result["has_changes"] is False
    assert result["changes"] == []


def test_delta_notifications_gate_change():
    prev = _run("run_prev", "sig_prev", "notes")
    prev.policy_hash_at_ingest = "policy_prev"
    current = _run("run_current", "sig_current", "notes")
    current.policy_hash_at_ingest = "policy_current"
    result = compute_delta_notifications(current, prev, "policy_current")
    codes = [change["code"] for change in result["changes"]]
    assert "gate_changed" in codes


def test_delta_notifications_drift_change():
    prev = _run("run_prev", "sig_prev", "notes")
    current = _run("run_current", "sig_current", "notes")
    prev.stability_report = {"drift_class": "none"}
    current.stability_report = {"drift_class": "high"}
    result = compute_delta_notifications(current, prev, "policy_hash")
    codes = [change["code"] for change in result["changes"]]
    assert "drift_class_changed" in codes


def test_delta_notifications_oracle_input_hash_change():
    prev = _run("run_prev", "sig_prev", "notes")
    current = _run("run_current", "sig_current", "notes")
    prev.oracle_output = {
        "signal_id": "sig_prev",
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {},
        "evidence": [],
        "flags": {},
        "provenance": {"input_hash": "aaaabbbb"},
    }
    current.oracle_output = {
        "signal_id": "sig_current",
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {},
        "evidence": [],
        "flags": {},
        "provenance": {"input_hash": "ccccdddd"},
    }
    result = compute_delta_notifications(current, prev, "policy_hash")
    codes = [change["code"] for change in result["changes"]]
    assert "oracle_input_hash_changed" in codes


def test_delta_notifications_risk_notes_change():
    prev = _run("run_prev", "sig_prev", "old notes")
    current = _run("run_current", "sig_current", "new notes")
    result = compute_delta_notifications(current, prev, "policy_hash")
    codes = [change["code"] for change in result["changes"]]
    assert "risk_notes_changed" in codes


def test_delta_notifications_ordering_and_caps():
    prev = _run("run_prev", "sig_prev", "old notes")
    prev.policy_hash_at_ingest = "policy_prev"
    prev.stability_report = {"drift_class": "none"}
    prev.oracle_output = {
        "signal_id": "sig_prev",
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {},
        "evidence": [],
        "flags": {},
        "provenance": {"input_hash": "aaaabbbb"},
    }

    current = _run("run_current", "sig_current", "new notes")
    current.policy_hash_at_ingest = "policy_current"
    current.stability_report = {"drift_class": "high"}
    current.oracle_output = {
        "signal_id": "sig_current",
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {},
        "evidence": [],
        "flags": {},
        "provenance": {"input_hash": "ccccdddd"},
    }

    result = compute_delta_notifications(current, prev, "policy_current")
    codes = [change["code"] for change in result["changes"]]
    assert codes == [
        "gate_changed",
        "drift_class_changed",
        "oracle_input_hash_changed",
        "risk_notes_changed",
    ]
    assert len(codes) <= 6
