from __future__ import annotations

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, DeferralStart, HumanAck
from webpanel.store import InMemoryStore


def _packet() -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-exec",
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


def test_execute_selected_action_micro_steps():
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet())
    run_id = resp["run_id"]
    _run_steps(run_id)

    run = webpanel_app.store.get(run_id)
    assert run is not None
    actions = run.last_step_result["actions"]
    selected_action_id = actions[0]["action_id"]

    webpanel_app._select_action(run_id, selected_action_id)
    run = webpanel_app.store.get(run_id)
    assert run is not None
    assert run.selected_action_id == selected_action_id

    if run.requires_human_confirmation and not run.human_ack:
        webpanel_app._record_ack(
            run_id,
            HumanAck(
                ack_mode="explicit_yes",
                ack_id="ack-1",
                ack_timestamp_utc="2026-02-03T00:00:00+00:00",
            ),
        )

    webpanel_app._start_deferral(run_id, DeferralStart(quota_max_actions=3))
    webpanel_app._step_deferral(run_id)
    run = webpanel_app.store.get(run_id)
    assert run is not None

    result = run.last_step_result
    assert result["kind"] == "execute_selected_action_v0"
    assert result["produces"]["artifact_kind"] in {
        "IntegrityRequest.v0",
        "QuestionSet.v0",
        "ObserveOnly.v0",
        "ActionComplete.v0",
        "AckReminder.v0",
    }
