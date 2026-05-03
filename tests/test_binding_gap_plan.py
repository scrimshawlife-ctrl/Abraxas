from __future__ import annotations

from abraxas.registry.binding_gap_plan import run_binding_gap_plan


def test_gap_plan_runs() -> None:
    result = run_binding_gap_plan()
    assert result["schema_version"] == "BindingGapPlan.v1"
    assert "plan" in result


def test_gap_plan_deterministic() -> None:
    first = run_binding_gap_plan()
    second = run_binding_gap_plan()
    assert first["canonical_hash"] == second["canonical_hash"]
