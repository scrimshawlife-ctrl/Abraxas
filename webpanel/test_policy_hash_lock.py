from __future__ import annotations

from fastapi.testclient import TestClient

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.store import InMemoryStore


def _packet() -> dict:
    return {
        "signal_id": "sig-policy",
        "timestamp_utc": "2026-02-03T00:00:00+00:00",
        "tier": "psychonaut",
        "lane": "canon",
        "payload": {"query": "policy"},
        "confidence": {"score": "0.1"},
        "provenance_status": "complete",
        "invariance_status": "pass",
        "drift_flags": [],
        "rent_status": "paid",
        "not_computable_regions": [],
    }


def test_policy_hash_lock(monkeypatch):
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()
    monkeypatch.setenv("ABX_DRIFT_PAUSE_THRESHOLD", "3")
    client = TestClient(webpanel_app.app)
    response = client.post("/api/v1/familiar/ingest", json=_packet())
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    run = webpanel_app.store.get(run_id)
    assert run is not None
    assert run.policy_hash_at_ingest

    monkeypatch.setenv("ABX_DRIFT_PAUSE_THRESHOLD", "4")
    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    assert "CHANGED" in response.text

    compare_resp = client.get(f"/compare?left={run_id}&right={run_id}")
    assert compare_resp.status_code == 200
    assert "Policy Drift" in compare_resp.text
