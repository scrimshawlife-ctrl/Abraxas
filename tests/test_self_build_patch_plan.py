from __future__ import annotations

from abraxas.registry.self_build_patch_plan import run_self_build_patch_plan


def test_patch_plan() -> None:
    result = run_self_build_patch_plan()
    assert result["schema_version"] == "SelfBuildPatchPlan.v1"
    assert result["plan_count"] > 0
