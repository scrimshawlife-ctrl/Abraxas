from __future__ import annotations

import hashlib
import json

from webpanel.explain_mode import build_run_brief
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


def _context(signal_id: str) -> DecisionContext:
    return DecisionContext(
        context_id=f"ctx_{signal_id}",
        source_signal_id=signal_id,
        created_at_utc="2026-02-03T00:00:00+00:00",
        risk_profile=RiskProfile(
            risk_of_action="medium",
            risk_of_inaction="low",
            risk_notes="",
        ),
        requires_human_confirmation=False,
        recommended_interaction_mode="advisor",
    )


def _run(run_id: str, signal_id: str) -> RunState:
    return RunState(
        run_id=run_id,
        created_at_utc="2026-02-03T00:00:00+00:00",
        phase=3,
        signal=_packet(signal_id),
        context=_context(signal_id),
        requires_human_confirmation=False,
    )


def _hash(obj: object) -> str:
    rendered = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def test_explain_mode_brief_is_deterministic():
    current_policy_hash = "policy_current_hash"
    run = _run("run_main", "sig_main")
    prev = _run("run_prev", "sig_prev")

    run.policy_hash_at_ingest = "policy_ingest_hash"
    run.session_active = False
    run.session_max_steps = 3
    run.session_steps_used = 1
    run.prefs = {
        "verbosity": "high",
        "risk_tolerance": "medium",
        "focus": ["gates", "oracle"],
        "show": ["oracle"],
        "hide": ["continuity"],
    }
    run.oracle_output = {
        "signal_id": "sig_main",
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {"alpha": 0.9, "beta": 0.4},
        "evidence": [{"source": "unit"}],
        "flags": {"suppressed": False, "alert": True},
        "provenance": {
            "input_hash": "deadbeefcafefeed",
            "policy_hash": "policy_current_hash",
            "operator_versions": {"op": "1.0.0"},
            "stability_status": {"drift_class": "none"},
        },
    }
    run.last_step_result = {
        "kind": "propose_actions_v0",
        "actions": [
            {
                "action_id": "act_1",
                "title": "Do the thing",
                "rationale": ["clear signal", "bounded risk"],
                "risk_flags": ["low_reversible"],
            }
        ],
    }

    brief_a = build_run_brief(run, prev, current_policy_hash)
    brief_b = build_run_brief(run, prev, current_policy_hash)

    assert len(brief_a["brief_lines"]) <= 12
    assert any("policy_ack_required" in line for line in brief_a["brief_lines"])
    assert brief_a["sections"]["oracle"]["tier"] == "psychonaut"
    assert brief_a["sections"]["oracle"]["lane"] == "canon"
    assert _hash(brief_a) == _hash(brief_b)
