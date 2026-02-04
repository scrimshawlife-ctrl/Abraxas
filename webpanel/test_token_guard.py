from __future__ import annotations

from fastapi.testclient import TestClient

from webpanel import app as webpanel_app


def _packet() -> dict:
    return {
        "signal_id": "sig-guard",
        "timestamp_utc": "2026-02-03T00:00:00+00:00",
        "tier": "psychonaut",
        "lane": "canon",
        "payload": {"query": "guard"},
        "confidence": {"score": "0.1"},
        "provenance_status": "complete",
        "invariance_status": "pass",
        "drift_flags": [],
        "rent_status": "paid",
        "not_computable_regions": [],
    }


def test_token_guard(monkeypatch):
    monkeypatch.setenv("ABX_PANEL_TOKEN", "t")
    client = TestClient(webpanel_app.app)

    assert client.get("/").status_code == 200

    response = client.post("/api/v1/familiar/ingest", json=_packet())
    assert response.status_code == 401

    response = client.post(
        "/api/v1/familiar/ingest",
        json=_packet(),
        headers={"X-ABX-Token": "t"},
    )
    assert response.status_code == 200
