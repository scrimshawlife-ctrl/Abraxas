from webpanel.core_bridge import core_ingest
from webpanel.models import AbraxasSignalPacket, RunState
from webpanel.policy import get_policy_snapshot
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


def _get_run() -> RunState:
    result = core_ingest(_packet().model_dump())
    return RunState(**result)


def _force_nondeterminism(final_payload: dict, cycle: int) -> None:
    if cycle == 1:
        final_payload["nondeterminism_probe"] = {"cycle": cycle}


def test_stability_report_includes_policy_hash_per_cycle():
    run = _get_run()
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
    run = _get_run()
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
    run = _get_run()
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
