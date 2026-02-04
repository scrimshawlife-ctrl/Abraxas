from __future__ import annotations

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.store import InMemoryStore


def test_emit_and_ingest_payload_helper():
    webpanel_app.store = InMemoryStore()
    webpanel_app.ledger = LedgerChain()
    _STEP_STATE.clear()

    payload = {"kind": "unit_test_payload"}
    run_id = webpanel_app._emit_and_ingest_payload(payload, tier="academic", lane="canon")
    assert run_id

    run = webpanel_app.store.get(run_id)
    assert run is not None
    assert run.signal.payload["kind"] == "unit_test_payload"
    assert run.signal.tier == "academic"
