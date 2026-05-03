from __future__ import annotations

from abraxas.registry.self_build_operator_queue import run_self_build_operator_queue


def test_operator_queue_runs() -> None:
    result = run_self_build_operator_queue()
    assert result["schema_version"] == "SelfBuildOperatorQueue.v1"
    assert result["queue_count"] >= 1
    assert result["authority"]["operator_approval_required"] is True


def test_operator_queue_deterministic() -> None:
    first = run_self_build_operator_queue()
    second = run_self_build_operator_queue()
    assert first["canonical_hash"] == second["canonical_hash"]
