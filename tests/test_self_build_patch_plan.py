from __future__ import annotations

import pytest


_XFAIL_DRIFT = (
    "Stateful test: self_build_* scans the live tree for NOT_COMPUTABLE "
    "artifacts and the pipeline has already upgraded them all (0 remain; 7 "
    "carry 'upgraded_from: NOT_COMPUTABLE'). Jev ruled leave-as-is (0.84). "
    "See docs/TEST_DEBT.md."
)

from abraxas.registry.self_build_patch_plan import run_self_build_patch_plan


@pytest.mark.xfail(reason=_XFAIL_DRIFT, strict=True)
def test_patch_plan() -> None:
    result = run_self_build_patch_plan()
    assert result["schema_version"] == "SelfBuildPatchPlan.v1"
    assert result["plan_count"] > 0
