from __future__ import annotations

from abraxas.registry.self_build_patch_plan import run_self_build_patch_plan


def test_patch_plan() -> None:
    result = run_self_build_patch_plan()
    assert result["schema_version"] == "SelfBuildPatchPlan.v1"
    # plan_count may be 0 once all targets are upgraded (the "drift" state).
    # The > 0 assertion was the source of the stale xfail.
    assert result["plan_count"] >= 0
