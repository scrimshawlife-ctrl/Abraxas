from __future__ import annotations

import pytest


_XFAIL_DRIFT = (
    "Stateful test: self_build_* scans the live tree for NOT_COMPUTABLE "
    "artifacts and the pipeline has already upgraded them all (0 remain; 7 "
    "carry 'upgraded_from: NOT_COMPUTABLE'). Jev ruled leave-as-is (0.84). "
    "See docs/TEST_DEBT.md."
)

from abraxas.registry.self_build_operator_queue import run_self_build_operator_queue


@pytest.mark.xfail(reason=_XFAIL_DRIFT, strict=True)
def test_operator_queue_runs() -> None:
    result = run_self_build_operator_queue()
    assert result["schema_version"] == "SelfBuildOperatorQueue.v1"
    assert result["queue_count"] >= 1
    assert result["authority"]["operator_approval_required"] is True


def test_operator_queue_deterministic() -> None:
    first = run_self_build_operator_queue()
    second = run_self_build_operator_queue()
    assert first["canonical_hash"] == second["canonical_hash"]
