from __future__ import annotations

import pytest


_XFAIL_DRIFT = (
    "Stateful test: self_build_* scans the live tree for NOT_COMPUTABLE "
    "artifacts and the pipeline has already upgraded them all (0 remain; 7 "
    "carry 'upgraded_from: NOT_COMPUTABLE'). Jev ruled leave-as-is (0.84). "
    "See docs/TEST_DEBT.md."
)

from abraxas.registry.self_build_approval_setter import run_self_build_approval_setter
from abraxas.registry.self_build_controlled_apply import run_self_build_controlled_apply
from abraxas.registry.self_build_operator_queue import run_self_build_operator_queue


def test_apply_fails_closed() -> None:
    run_self_build_approval_setter([], [])
    result = run_self_build_controlled_apply()
    assert result["status"] == "NO_APPROVED_ITEMS"
    assert result["applied_count"] == 0


@pytest.mark.xfail(reason=_XFAIL_DRIFT, strict=True)
def test_apply_one_item() -> None:
    queue = run_self_build_operator_queue()
    first_id = queue["items"][0]["approval_id"]
    run_self_build_approval_setter([first_id], [])
    result = run_self_build_controlled_apply()
    assert result["status"] == "APPLIED"
    assert result["applied_count"] == 1
