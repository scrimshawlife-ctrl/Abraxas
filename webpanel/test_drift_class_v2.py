from __future__ import annotations

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket
from webpanel.policy import get_policy_snapshot
from webpanel.store import InMemoryStore
from webpanel.stability import run_stabilization


def _packet() -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-drift",
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={"alpha": {"beta": 1}},
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def test_drift_class_none():
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet())
    run = webpanel_app.store.get(resp["run_id"])
    assert run is not None
    snapshot = get_policy_snapshot()
    report = run_stabilization(
        run,
        cycles=12,
        operators=["extract_structure_v0", "compress_signal_v0", "propose_actions_v0"],
        policy_hash=snapshot["policy_hash"],
    )
    assert report["drift_class"] == "none"
    assert report["invariance"]["distinct_input_hashes"] == 1


def test_drift_class_input_variation():
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    resp = webpanel_app.ingest(_packet())
    run = webpanel_app.store.get(resp["run_id"])
    assert run is not None
    snapshot = get_policy_snapshot()

    def mutator(run_state, cycle):
        if cycle == 1:
            run_state.signal.payload["alpha"]["beta"] = 2

    report = run_stabilization(
        run,
        cycles=3,
        operators=["extract_structure_v0", "compress_signal_v0", "propose_actions_v0"],
        policy_hash=snapshot["policy_hash"],
        test_mutator=mutator,
    )
    assert report["drift_class"] == "input_variation"
    assert report["invariance"]["distinct_input_hashes"] > 1
