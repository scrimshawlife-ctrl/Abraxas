from __future__ import annotations

import copy
from hashlib import sha256

from abraxas.canary.activation_runner import build_canary_activation_packet_run
from abraxas.core.canonical import canonical_json


def _inputs(status: str = "recommend_approve_for_activation_review"):
    review = {
        "recommendations": [
            {
                "recommendation_id": "rec1",
                "overlay_id": "ov1",
                "entry_id": "e1",
                "proposal_id": "p1",
                "source_key": "s1",
                "status": status,
                "basis": {
                    "improvement_direction": "improved",
                    "delta_error": -0.02,
                    "scores_used": 4,
                    "baseline_error": 0.3,
                    "simulated_error": 0.28,
                    "forecasts_matched": 5,
                },
            }
        ]
    }
    overlays = {"overlays": [{"overlay_id": "ov1", "entry_id": "e1", "proposal_id": "p1", "source_key": "s1"}]}
    ledger = {"entries": [{"entry_id": "e1", "x": 1}]}
    return review, overlays, ledger


def test_approved_creates_packet_and_preserves_fields() -> None:
    r, o, l = _inputs()
    run = build_canary_activation_packet_run(r, o, l)
    assert run["counts"]["packets_created"] == 1
    p = run["packets"][0]
    assert p["summary"] == {"improvement_direction": "improved", "delta_error": -0.02, "scores_used": 4}
    assert p["evidence"] == {"baseline_error": 0.3, "simulated_error": 0.28, "forecasts_matched": 5}


def test_hold_reject_not_computable_skipped() -> None:
    for st in ["recommend_hold", "recommend_reject", "not_computable"]:
        r, o, l = _inputs(st)
        run = build_canary_activation_packet_run(r, o, l)
        assert run["counts"]["packets_created"] == 0
        assert run["counts"]["skipped"] == 1
        assert run["skipped_recommendations"][0]["reason"] == f"not_approved_for_activation_review:{st}"


def test_missing_overlay_skipped() -> None:
    r, _, l = _inputs()
    run = build_canary_activation_packet_run(r, {"overlays": []}, l)
    assert run["counts"]["packets_created"] == 0
    assert run["skipped_recommendations"][0]["reason"] == "missing_overlay"


def test_packet_id_determinism_authority_counts_immutability_and_byte_identical(tmp_path) -> None:
    r, o, l = _inputs()
    r0, o0, l0 = copy.deepcopy(r), copy.deepcopy(o), copy.deepcopy(l)
    run_a = build_canary_activation_packet_run(r, o, l)
    run_b = build_canary_activation_packet_run(r, o, l)
    assert canonical_json(run_a) == canonical_json(run_b)

    packet = run_a["packets"][0]
    payload = {
        "packet_version": "CanaryActivationPacket.v1",
        "overlay_id": packet["overlay_id"],
        "entry_id": packet["entry_id"],
        "proposal_id": packet["proposal_id"],
        "source_key": packet["source_key"],
        "recommendation_status": packet["recommendation_status"],
        "summary": packet["summary"],
        "evidence": packet["evidence"],
        "lineage": packet["lineage"],
        "review": packet["review"],
        "authority": packet["authority"],
    }
    assert packet["packet_id"] == sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    assert run_a["authority"] == {
        "activation_packet_generation": True,
        "overlay_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }
    assert run_a["counts"] == {"recommendations_total": 1, "packets_created": 1, "skipped": 0}
    assert (r, o, l) == (r0, o0, l0)

    p1 = tmp_path / "one.json"
    p2 = tmp_path / "two.json"
    p1.write_text(canonical_json(run_a) + "\n", encoding="utf-8")
    p2.write_text(canonical_json(run_a) + "\n", encoding="utf-8")
    assert p1.read_bytes() == p2.read_bytes()
