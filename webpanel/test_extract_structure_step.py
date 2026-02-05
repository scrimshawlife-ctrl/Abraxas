from __future__ import annotations

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, DeferralStart
from webpanel.store import InMemoryStore


def _packet() -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-structure",
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={
            "alpha": {"beta": 1, "url": "https://example.com"},
            "claims": [{"id": "c1", "text": "x"}],
            "empty": {},
            "none": None,
        },
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def test_extract_structure_step():
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet())
    run_id = resp["run_id"]

    webpanel_app._start_deferral(run_id, DeferralStart(quota_max_actions=2))
    webpanel_app._step_deferral(run_id)

    run = webpanel_app.store.get(run_id)
    assert run is not None
    assert run.last_step_result is not None
    result = run.last_step_result
    assert result["kind"] == "extract_structure_v0"
    assert result["keys_topology"]["paths_count"] > 0
    assert any(metric["path"].endswith(".beta") for metric in result["numeric_metrics"])
    assert any(ref["path"].endswith(".url") for ref in result["evidence_refs"])
    assert any(u["path"].endswith(".empty") for u in result["unknowns"])
    assert any(u["path"].endswith(".none") for u in result["unknowns"])
    assert result["claims_present"] is True
    assert len(result["claims_preview"]) == 1


def test_extract_structure_deterministic():
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    resp_a = webpanel_app.ingest(_packet())
    resp_b = webpanel_app.ingest(_packet())

    webpanel_app._start_deferral(resp_a["run_id"], DeferralStart(quota_max_actions=2))
    webpanel_app._step_deferral(resp_a["run_id"])

    webpanel_app._start_deferral(resp_b["run_id"], DeferralStart(quota_max_actions=2))
    webpanel_app._step_deferral(resp_b["run_id"])

    run_a = webpanel_app.store.get(resp_a["run_id"])
    run_b = webpanel_app.store.get(resp_b["run_id"])

    assert run_a is not None and run_b is not None
    assert run_a.last_step_result == run_b.last_step_result
