from __future__ import annotations

import json

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, DeferralStart
from webpanel.store import InMemoryStore
from webpanel._session_helpers import satisfy_panel_gates


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
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet())
    run_id = resp["run_id"]

    # The panel gates session-dependent steps; the session must be active BEFORE any of
    # them is called, so it is opened as soon as the run id exists.
    satisfy_panel_gates(webpanel_app.store.get(run_id), ledger=webpanel_app.ledger)
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


def test_sample_packet_route():
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    response = webpanel_app.ui_sample_packet()
    payload = json.loads(response.body.decode("utf-8"))
    packet = AbraxasSignalPacket.model_validate(payload)
    resp = webpanel_app.ingest(packet)
    assert resp["run_id"]
