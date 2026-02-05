from __future__ import annotations

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.lineage import get_lineage
from webpanel.models import AbraxasSignalPacket
from webpanel.store import InMemoryStore


def _packet(signal_id: str, invariance: str) -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id=signal_id,
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={"query": "continuity"},
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status=invariance,
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def test_continuity_linking():
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    resp_a = webpanel_app.ingest(_packet("sig-a", "fail"))
    run_a = webpanel_app.store.get(resp_a["run_id"])
    assert run_a is not None

    resp_b = webpanel_app._ingest_packet(_packet("sig-b", "pass"), prev_run_id=run_a.run_id)
    run_b = webpanel_app.store.get(resp_b["run_id"])
    assert run_b is not None
    assert run_b.prev_run_id == run_a.run_id
    assert run_b.continuity_reason == "new_packet_supersedes_previous"

    lineage = get_lineage(run_b.run_id, webpanel_app.store)
    assert [run.run_id for run in lineage] == [run_b.run_id, run_a.run_id]

    events_b = list(webpanel_app.ledger.list_events(run_b.run_id))
    assert any(event.event_type == "continuity_linked" for event in events_b)

    events_a = list(webpanel_app.ledger.list_events(run_a.run_id))
    assert any(event.event_type == "superseded_by" for event in events_a)
