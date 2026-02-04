from __future__ import annotations

import pytest

from webpanel.core_bridge import core_ingest
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, RunState
from webpanel.preference_kernel import (
    apply_prefs_update,
    build_consideration_view,
    normalize_prefs,
    prefs_hash_prefix,
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


def test_prefs_update_and_ledger_event():
    run = _run("sig-prefs")
    ledger = LedgerChain()
    new_prefs = {
        "verbosity": "low",
        "risk_tolerance": "high",
        "focus": "drift,evidence",
        "show": ["oracle", "continuity"],
        "hide": [],
    }
    prefs = apply_prefs_update(
        run=run,
        new_prefs=new_prefs,
        ledger=ledger,
        event_id="ev_prefs",
        timestamp_utc="2026-02-03T00:00:00+00:00",
    )
    assert prefs["verbosity"] == "low"
    assert prefs["risk_tolerance"] == "high"
    assert prefs["focus"] == ["drift", "evidence"]
    events = ledger.list_events(run.run_id)
    assert events[-1].event_type == "prefs_update"
    assert events[-1].data["new_prefs_hash_prefix"] == prefs_hash_prefix(prefs)


def test_invalid_prefs_rejected():
    with pytest.raises(ValueError):
        normalize_prefs({"bad_key": "x"})


def test_verbosity_affects_rationale_display():
    consideration = {
        "proposal_id": "p1",
        "rationale": [f"r{i}" for i in range(7)],
        "dependencies": [],
        "counterfactuals": [],
        "risk_flags": [],
        "evidence_refs": [],
        "provenance": {},
    }
    low = normalize_prefs({"verbosity": "low"})
    medium = normalize_prefs({"verbosity": "medium"})
    high = normalize_prefs({"verbosity": "high"})
    view_low = build_consideration_view(consideration, low)
    view_medium = build_consideration_view(consideration, medium)
    view_high = build_consideration_view(consideration, high)
    assert len(view_low["rationale_display"]) == 3
    assert len(view_medium["rationale_display"]) == 5
    assert len(view_high["rationale_display"]) == 7
