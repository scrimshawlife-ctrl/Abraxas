from __future__ import annotations

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, DeferralStart
from webpanel.store import InMemoryStore
from webpanel._session_helpers import satisfy_panel_gates


def _packet() -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-select",
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


def test_select_action_builds_checklist():
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet())
    run_id = resp["run_id"]
    # The panel gates session-dependent steps; the session must be active BEFORE any of
    # them is called, so it is opened as soon as the run id exists.
    satisfy_panel_gates(webpanel_app.store.get(run_id), ledger=webpanel_app.ledger)
    _run_steps(run_id)

    run = webpanel_app.store.get(run_id)
    assert run is not None
    actions = run.last_step_result["actions"]
    selected_action_id = actions[0]["action_id"]

    webpanel_app._select_action(run_id, selected_action_id)
    run = webpanel_app.store.get(run_id)
    assert run is not None
    assert run.selected_action_id == selected_action_id
    assert run.execution_checklist["kind"] == "ExecutionChecklist.v0"

    events = list(webpanel_app.ledger.read_all())
    assert any(event.get("event_type") == "action_selected" for event in events)

    checklist_first = run.execution_checklist
    webpanel_app._select_action(run_id, selected_action_id)
    run = webpanel_app.store.get(run_id)
    assert run is not None
    assert run.execution_checklist == checklist_first
