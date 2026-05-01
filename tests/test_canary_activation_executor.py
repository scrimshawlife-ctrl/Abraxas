from __future__ import annotations

import copy
from hashlib import sha256
from pathlib import Path

from abraxas.canary.execution_runner import run_activation_executor
from abraxas.core.canonical import canonical_json


def _packet(status: str = "recommend_approve_for_activation_review") -> dict:
    return {
        "packet_id": "pkt1",
        "overlay_id": "ov1",
        "overlay_hash": "oh1",
        "simulation_hash": "sh1",
        "recommendation_id": "rec1",
        "source_key": "s1",
        "recommendation_status": status,
        "summary": {"x": 1},
        "evidence": {"y": 2},
        "authority": {
            "activation_packet_generation": True,
            "overlay_activation": False,
            "baseline_mutation": False,
            "runtime_config_write": False,
            "promotion": False,
            "execution": False,
            "scheduler": False,
        },
        "lineage": {
            "recommendation_id": "rec1",
            "simulation_hash": "sh1",
            "ledger_entry_hash": None,
        },
    }


def _input(packet: dict) -> dict:
    return {"schema_version": "CanaryActivationPacketRun.v1", "packets": [packet]}


def test_approved_packet_execution_and_determinism_and_bytes() -> None:
    inp = _input(_packet())
    r1 = run_activation_executor(inp, created_at="2026-01-01T00:00:00Z", scope_id="scopeA")
    r2 = run_activation_executor(inp, created_at="2026-01-01T00:00:00Z", scope_id="scopeA")
    assert r1["counts"]["executions"] == 1
    assert r1["counts"]["skipped"] == 0
    assert r1["executions"][0]["execution_status"] == "canary_applied"
    assert r1["executions"][0]["execution_id"] == r2["executions"][0]["execution_id"]
    assert canonical_json(r1) == canonical_json(r2)


def test_sandbox_write_and_hash(tmp_path: Path) -> None:
    inp = _input(_packet())
    sandbox = tmp_path / "sb"
    run = run_activation_executor(inp, created_at="2026-01-01T00:00:00Z", scope_id="scopeA", sandbox_root=str(sandbox))
    ex = run["executions"][0]
    receipt = Path(ex["applied_artifact"]["artifact_path"])
    assert receipt.exists()
    assert sandbox in receipt.parents
    assert ex["applied_artifact"]["artifact_hash"] == sha256(receipt.read_bytes()).hexdigest()


def test_in_memory_mode_invalid_packet_authority_immutability_counts_sorting_and_writes(tmp_path: Path) -> None:
    good = _packet()
    bad = _packet()
    bad.pop("packet_id")
    bad["source_key"] = "s0"
    blocked = _packet()
    blocked["source_key"] = "s2"
    blocked["authority"]["promotion"] = True
    hold = _packet(status="recommend_hold")
    hold["source_key"] = "s3"
    inp = {"schema_version": "CanaryActivationPacketRun.v1", "packets": [hold, good, blocked, bad]}
    inp0 = copy.deepcopy(inp)

    run = run_activation_executor(inp, created_at="2026-01-01T00:00:00Z", scope_id="scopeA")
    assert run["executions"][0]["applied_artifact"]["artifact_path"] is None
    assert run["executions"][0]["applied_artifact"]["artifact_hash"]
    assert run["authority"] == {
        "canary_activation": True,
        "baseline_mutation": False,
        "runtime_write": False,
        "scheduler_registration": False,
        "promotion": False,
        "production_execution": False,
    }
    assert run["counts"]["input_packets"] == 4
    assert run["counts"]["executions"] == 1
    assert run["counts"]["skipped"] == 3
    reasons = [s["reason"] for s in run["skipped"]]
    assert "invalid_packet" in reasons
    assert "not_approved_for_execution" in reasons
    assert any(r.startswith("authority_boundary_violation:") for r in reasons)
    assert inp == inp0

    sorted_exec = sorted(run["executions"], key=lambda x: (x["source_key"], x["execution_id"]))
    assert run["executions"] == sorted_exec
    sorted_skip = sorted(run["skipped"], key=lambda x: (str(x.get("source_key") or ""), str(x.get("overlay_id") or ""), str(x.get("packet_id") or ""), x["reason"]))
    assert run["skipped"] == sorted_skip

    files = [p for p in tmp_path.rglob("*") if p.is_file()]
    assert files == []
