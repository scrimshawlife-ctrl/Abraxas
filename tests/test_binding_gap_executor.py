from __future__ import annotations

from abraxas.registry.binding_gap_executor import run_binding_gap_executor


def test_executor_runs() -> None:
    result = run_binding_gap_executor()
    assert result["schema_version"] == "BindingGapExecutionReport.v1"
    assert "by_priority" in result


def test_executor_deterministic() -> None:
    first = run_binding_gap_executor()
    second = run_binding_gap_executor()
    assert first["canonical_hash"] == second["canonical_hash"]
