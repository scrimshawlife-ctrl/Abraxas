from __future__ import annotations

from webpanel.compare import compare_runs
from webpanel.core_bridge import core_ingest
from webpanel.models import AbraxasSignalPacket, RunState


def _packet(signal_id: str) -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id=signal_id,
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


def _run(signal_id: str) -> RunState:
    result = core_ingest(_packet(signal_id).model_dump())
    return RunState(**result)


def _oracle_output(
    *,
    signal_id: str,
    score: float,
    flags: dict,
    evidence: list,
    input_hash: str,
    policy_hash: str,
    stability_status: dict,
) -> dict:
    return {
        "signal_id": signal_id,
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {"score": score, "label": "alpha"},
        "evidence": evidence,
        "flags": flags,
        "provenance": {
            "input_hash": input_hash,
            "policy_hash": policy_hash,
            "operator_versions": {"extract_structure_v0": "v0"},
            "stability_status": stability_status,
        },
    }


def test_compare_oracle_diffs():
    left = _run("sig-left")
    right = _run("sig-right")
    left.oracle_output = _oracle_output(
        signal_id="sig-left",
        score=0.4,
        flags={"suppressed": False},
        evidence=["ref-a"],
        input_hash="input-left",
        policy_hash="policy-left",
        stability_status={"passed": True, "drift_class": "none"},
    )
    right.oracle_output = _oracle_output(
        signal_id="sig-right",
        score=0.9,
        flags={"suppressed": True},
        evidence=["ref-b"],
        input_hash="input-right",
        policy_hash="policy-right",
        stability_status={"passed": False, "drift_class": "input_variation"},
    )

    compare = compare_runs(left, right)
    oracle = compare["oracle"]
    assert oracle["present_left"] is True
    assert oracle["present_right"] is True
    assert "suppressed=True" in oracle["flags_added"]
    assert "suppressed=False" in oracle["flags_removed"]
    assert "ref-b" in oracle["evidence_added"]
    assert "ref-a" in oracle["evidence_removed"]
    assert oracle["indicator_deltas"][0]["path"] == "score"
    assert oracle["provenance_diffs"]["input_hash"]["changed"] is True
    assert oracle["provenance_diffs"]["policy_hash"]["changed"] is True
