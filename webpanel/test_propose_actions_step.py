from __future__ import annotations

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, DeferralStart
from webpanel.store import InMemoryStore


def _packet() -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-actions",
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={
            "alpha": {"beta": 1, "url": "https://example.com"},
            "none": None,
        },
        confidence={"score": "0.5"},
        provenance_status="partial",
        invariance_status="not_evaluated",
        drift_flags=["x"],
        rent_status="paid",
        not_computable_regions=[],
    )


def _run_steps(run_id: str) -> None:
    webpanel_app._start_deferral(run_id, DeferralStart(quota_max_actions=3))
    webpanel_app._step_deferral(run_id)
    webpanel_app._step_deferral(run_id)
    webpanel_app._step_deferral(run_id)


def test_propose_actions_step():
    webpanel_app.store = InMemoryStore()
    webpanel_app.ledger = LedgerChain()
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet())
    _run_steps(resp["run_id"])

    run = webpanel_app.store.get(resp["run_id"])
    assert run is not None
    result = run.last_step_result
    assert result is not None
    assert result["kind"] == "propose_actions_v0"
    actions = result["actions"]
    assert 2 <= len(actions) <= 3
    assert actions[0]["kind"] == "request_missing_integrity"


def test_propose_actions_determinism():
    webpanel_app.store = InMemoryStore()
    webpanel_app.ledger = LedgerChain()
    _STEP_STATE.clear()

    resp_a = webpanel_app.ingest(_packet())
    resp_b = webpanel_app.ingest(_packet())

    _run_steps(resp_a["run_id"])
    _run_steps(resp_b["run_id"])

    run_a = webpanel_app.store.get(resp_a["run_id"])
    run_b = webpanel_app.store.get(resp_b["run_id"])

    assert run_a is not None and run_b is not None
    assert run_a.last_step_result == run_b.last_step_result
