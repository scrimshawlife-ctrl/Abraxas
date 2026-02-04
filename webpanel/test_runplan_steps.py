from __future__ import annotations

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, DeferralStart
from webpanel.store import InMemoryStore


def _packet(with_unknowns: bool) -> AbraxasSignalPacket:
    not_computable = []
    if with_unknowns:
        not_computable = [{"region_id": "r1", "reason_code": "missing"}]
    return AbraxasSignalPacket(
        signal_id="sig-plan",
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={"query": "plan"},
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=not_computable,
    )


def test_runplan_steps_and_quota():
    webpanel_app.store = InMemoryStore()
    webpanel_app.ledger = LedgerChain()
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet(with_unknowns=True))
    run_id = resp["run_id"]

    run = webpanel_app.store.get(run_id)
    assert run is not None
    assert run.runplan is not None
    kinds = [step.kind for step in run.runplan.steps]
    assert "surface_unknowns" in kinds

    webpanel_app._start_deferral(run_id, DeferralStart(quota_max_actions=2))
    webpanel_app._step_deferral(run_id)
    webpanel_app._step_deferral(run_id)

    run = webpanel_app.store.get(run_id)
    assert run is not None
    assert run.actions_taken == 2
    assert run.last_step_result is not None
    assert run.pause_reason == "quota_exhausted"


def test_runplan_hash_determinism():
    webpanel_app.store = InMemoryStore()
    webpanel_app.ledger = LedgerChain()
    _STEP_STATE.clear()

    resp_a = webpanel_app.ingest(_packet(with_unknowns=False))
    resp_b = webpanel_app.ingest(_packet(with_unknowns=False))

    run_a = webpanel_app.store.get(resp_a["run_id"])
    run_b = webpanel_app.store.get(resp_b["run_id"])

    assert run_a is not None and run_b is not None
    assert run_a.runplan is not None and run_b.runplan is not None
    assert run_a.runplan.deterministic_hash == run_b.runplan.deterministic_hash
