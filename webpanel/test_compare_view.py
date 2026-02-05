from __future__ import annotations

from fastapi.testclient import TestClient

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, DeferralStart
from webpanel.store import InMemoryStore


def _packet(signal_id: str, payload: dict) -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id=signal_id,
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload=payload,
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def _run_extract_compress(run_id: str) -> None:
    webpanel_app._start_deferral(run_id, DeferralStart(quota_max_actions=3))
    webpanel_app._step_deferral(run_id)
    webpanel_app._step_deferral(run_id)


def test_compare_view():
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    resp_a = webpanel_app.ingest(_packet("sig-a", {"a": 1, "url": "https://x", "empty": {}}))
    _run_extract_compress(resp_a["run_id"])

    resp_b = webpanel_app._ingest_packet(
        _packet("sig-b", {"a": 2, "b": 3, "url": "https://x", "none": None}),
        prev_run_id=resp_a["run_id"],
    )
    _run_extract_compress(resp_b["run_id"])

    client = TestClient(webpanel_app.app)
    response = client.get(f"/compare?left={resp_a['run_id']}&right={resp_b['run_id']}")
    assert response.status_code == 200
    assert "Added paths" in response.text
    assert "b" in response.text
    assert "a" in response.text
