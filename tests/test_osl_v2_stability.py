from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket
from webpanel.policy import get_policy_snapshot
from webpanel.store import InMemoryStore
from webpanel.stability import run_stabilization


def _packet() -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-stability-v2",
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


def _reset_and_get_run():
    webpanel_app.store = InMemoryStore()
    webpanel_app.ledger = LedgerChain()
    _STEP_STATE.clear()
    resp = webpanel_app.ingest(_packet())
    run = webpanel_app.store.get(resp["run_id"])
    assert run is not None
    return run


def _force_nondeterminism(final_payload: dict, cycle: int) -> None:
    if cycle == 1:
        final_payload["nondeterminism_probe"] = {"cycle": cycle}


def test_stability_report_includes_policy_hash_per_cycle():
    run = _reset_and_get_run()
    snapshot = get_policy_snapshot()
    report = run_stabilization(
        run,
        cycles=3,
        operators=["extract_structure_v0", "compress_signal_v0", "propose_actions_v0"],
        policy_hash=snapshot["policy_hash"],
    )
    for entry in report["results"]:
        assert entry["policy_hash"] == snapshot["policy_hash"]


def test_drift_class_nondeterminism():
    run = _reset_and_get_run()
    snapshot = get_policy_snapshot()
    report = run_stabilization(
        run,
        cycles=3,
        operators=["extract_structure_v0", "compress_signal_v0", "propose_actions_v0"],
        policy_hash=snapshot["policy_hash"],
        test_finalizer=_force_nondeterminism,
    )
    assert report["drift_class"] == "nondeterminism"


def test_drift_class_policy_change():
    run = _reset_and_get_run()
    snapshot = get_policy_snapshot()
    report = run_stabilization(
        run,
        cycles=3,
        operators=["extract_structure_v0", "compress_signal_v0", "propose_actions_v0"],
        policy_hash=snapshot["policy_hash"],
        prior_report={"policy_hash": "prev_policy_hash"},
        test_finalizer=_force_nondeterminism,
    )
    assert report["drift_class"] == "policy_change"
