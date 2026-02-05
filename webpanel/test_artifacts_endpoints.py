from __future__ import annotations

import json

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket
from webpanel.store import InMemoryStore


def _packet() -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-artifact",
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={"query": "artifact"},
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def test_artifacts_endpoints():
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet())
    run_id = resp["run_id"]

    packet_response = webpanel_app.ui_packet_json(run_id)
    packet_payload = json.loads(packet_response.body.decode("utf-8"))
    assert packet_payload["signal_id"] == "sig-artifact"

    ledger_response = webpanel_app.ui_ledger_json(run_id)
    ledger_payload = json.loads(ledger_response.body.decode("utf-8"))
    assert ledger_payload["run_id"] == run_id
    assert isinstance(ledger_payload["events"], list)
