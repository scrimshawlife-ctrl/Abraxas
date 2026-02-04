from __future__ import annotations

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, DeferralStart
from webpanel.store import InMemoryStore


def _packet() -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-1",
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={"query": "alpha"},
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def test_core_bridge_ingest_and_quota_boundary():
    webpanel_app.store = InMemoryStore()
    webpanel_app.ledger = LedgerChain()
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet())
    run_id = resp["run_id"]

    run = webpanel_app.store.get(run_id)
    assert run is not None
    assert run.run_id == run_id
    assert run.context.context_id
    assert run.signal.tier == "psychonaut"
    assert run.pause_required is False

    webpanel_app.defer_start(run_id, DeferralStart(quota_max_actions=2))
    webpanel_app.defer_step(run_id)
    webpanel_app.defer_step(run_id)

    run = webpanel_app.store.get(run_id)
    assert run is not None
    assert run.actions_taken == 2
    assert run.pause_required is True
    assert run.pause_reason == "quota_exhausted"
