from __future__ import annotations

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket
from webpanel.store import InMemoryStore
from webpanel.stability import run_stabilization


def _packet() -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-stability",
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={"alpha": {"beta": 1, "url": "https://example.com"}},
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def test_stability_report_passes():
    webpanel_app.store = InMemoryStore()
    webpanel_app.ledger = LedgerChain()
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet())
    run = webpanel_app.store.get(resp["run_id"])
    assert run is not None

    report = run_stabilization(run, cycles=12)
    assert report["kind"] == "StabilityReport.v0"
    assert report["invariance"]["passed"] is True
    assert report["invariance"]["distinct_final_hashes"] == 1
