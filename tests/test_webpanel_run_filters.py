from __future__ import annotations

from webpanel.core_bridge import core_ingest
from webpanel.models import AbraxasSignalPacket, RunState
from webpanel.run_filters import filter_runs


def _packet(signal_id: str, *, tier: str = "psychonaut", lane: str = "canon") -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id=signal_id,
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier=tier,
        lane=lane,
        payload={"alpha": {"beta": 1}},
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def _run(signal_id: str, created_at: str, *, tier: str = "psychonaut", lane: str = "canon") -> RunState:
    result = core_ingest(_packet(signal_id, tier=tier, lane=lane).model_dump())
    run = RunState(**result)
    run.created_at_utc = created_at
    run.signal.signal_id = signal_id
    run.signal.tier = tier
    run.signal.lane = lane
    return run


def _oracle_output(
    *,
    signal_id: str,
    tier: str,
    lane: str,
    drift_class: str,
    flags: object,
    evidence: list,
) -> dict:
    return {
        "signal_id": signal_id,
        "tier": tier,
        "lane": lane,
        "indicators": {"score": 0.5},
        "evidence": evidence,
        "flags": flags,
        "provenance": {
            "input_hash": f"input-{signal_id}",
            "policy_hash": f"policy-{signal_id}",
            "operator_versions": {"extract_structure_v0": "v0"},
            "stability_status": {"passed": True, "drift_class": drift_class},
        },
    }


def _runs_fixture():
    run_a = _run("sig-a", "2026-02-03T00:00:02+00:00")
    run_a.oracle_output = _oracle_output(
        signal_id="sig-a",
        tier="enterprise",
        lane="forecast",
        drift_class="none",
        flags={"evidence_missing": True},
        evidence=[],
    )
    run_b = _run("sig-b", "2026-02-03T00:00:02+00:00")
    run_b.oracle_output = _oracle_output(
        signal_id="sig-b",
        tier="psychonaut",
        lane="shadow",
        drift_class="policy_change",
        flags=["flag_a"],
        evidence=["ref-a"],
    )
    run_c = _run("sig-c", "2026-02-03T00:00:01+00:00", tier="academic")
    run_c.stability_report = {"drift_class": "nondeterminism"}
    return [run_b, run_c, run_a]


def test_filter_has_oracle_and_ordering():
    runs = _runs_fixture()
    filtered = filter_runs(runs, {"has_oracle": "yes"})
    assert [run.signal.signal_id for run in filtered] == ["sig-a", "sig-b"]


def test_filter_tier_prefers_oracle():
    runs = _runs_fixture()
    filtered = filter_runs(runs, {"tier": "enterprise"})
    assert [run.signal.signal_id for run in filtered] == ["sig-a"]


def test_filter_lane_prefers_oracle():
    runs = _runs_fixture()
    filtered = filter_runs(runs, {"lane": "forecast"})
    assert [run.signal.signal_id for run in filtered] == ["sig-a"]


def test_filter_drift_class_sources():
    runs = _runs_fixture()
    filtered_oracle = filter_runs(runs, {"drift_class": "policy_change"})
    assert [run.signal.signal_id for run in filtered_oracle] == ["sig-b"]

    filtered_stability = filter_runs(runs, {"drift_class": "nondeterminism"})
    assert [run.signal.signal_id for run in filtered_stability] == ["sig-c"]


def test_filter_flags_and_evidence():
    runs = _runs_fixture()
    filtered_flags = filter_runs(runs, {"flag": "evidence_missing"})
    assert [run.signal.signal_id for run in filtered_flags] == ["sig-a"]

    filtered_missing = filter_runs(runs, {"evidence": "missing"})
    assert [run.signal.signal_id for run in filtered_missing] == ["sig-a"]

    filtered_present = filter_runs(runs, {"evidence": "present"})
    assert [run.signal.signal_id for run in filtered_present] == ["sig-b"]
