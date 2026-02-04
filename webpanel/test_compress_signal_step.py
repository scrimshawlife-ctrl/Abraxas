from __future__ import annotations

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, DeferralStart
from webpanel.store import InMemoryStore


def _packet() -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-compress",
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={
            "alpha": {"beta": 3, "url": "https://example.com"},
            "empty": {},
            "none": None,
        },
        confidence={"score": "0.5"},
        provenance_status="partial",
        invariance_status="fail",
        drift_flags=["drift_a"],
        rent_status="paid",
        not_computable_regions=[],
    )


def test_compress_signal_step():
    webpanel_app.store = InMemoryStore()
    webpanel_app.ledger = LedgerChain()
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet())
    run_id = resp["run_id"]

    webpanel_app._start_deferral(run_id, DeferralStart(quota_max_actions=3))
    webpanel_app._step_deferral(run_id)
    webpanel_app._step_deferral(run_id)

    run = webpanel_app.store.get(run_id)
    assert run is not None
    result = run.last_step_result
    assert result is not None
    assert result["kind"] == "compress_signal_v0"
    assert result["plan_pressure"]["score"] == 0.9
    assert result["salient_metrics"]
    assert result["evidence_surface"]["url"]
    assert result["next_questions"]


def test_compress_signal_determinism():
    webpanel_app.store = InMemoryStore()
    webpanel_app.ledger = LedgerChain()
    _STEP_STATE.clear()

    resp_a = webpanel_app.ingest(_packet())
    resp_b = webpanel_app.ingest(_packet())

    webpanel_app._start_deferral(resp_a["run_id"], DeferralStart(quota_max_actions=3))
    webpanel_app._step_deferral(resp_a["run_id"])
    webpanel_app._step_deferral(resp_a["run_id"])

    webpanel_app._start_deferral(resp_b["run_id"], DeferralStart(quota_max_actions=3))
    webpanel_app._step_deferral(resp_b["run_id"])
    webpanel_app._step_deferral(resp_b["run_id"])

    run_a = webpanel_app.store.get(resp_a["run_id"])
    run_b = webpanel_app.store.get(resp_b["run_id"])

    assert run_a is not None and run_b is not None
    assert run_a.last_step_result == run_b.last_step_result
