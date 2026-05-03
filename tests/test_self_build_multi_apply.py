from __future__ import annotations

from abraxas.registry.self_build_approval_setter import run_self_build_approval_setter
from abraxas.registry.self_build_multi_apply import run_self_build_multi_apply
from abraxas.registry.self_build_operator_queue import run_self_build_operator_queue


def test_no_approvals_returns_no_approved_items() -> None:
    run_self_build_approval_setter([], [])
    result = run_self_build_multi_apply()
    assert result["status"] == "NO_APPROVED_ITEMS"


def test_duplicate_target_fails_closed() -> None:
    queue = run_self_build_operator_queue()
    first_id = queue["items"][0]["approval_id"]
    run_self_build_approval_setter([first_id, first_id], [])
    result = run_self_build_multi_apply()
    assert result["status"] == "NOT_COMPUTABLE"


def test_one_approved_applies_one_target() -> None:
    queue = run_self_build_operator_queue()
    first_id = queue["items"][0]["approval_id"]
    run_self_build_approval_setter([first_id], [])
    result = run_self_build_multi_apply()
    assert result["status"] == "APPLIED"
    assert result["applied_count"] == 1


def test_multi_approved_ids_apply_deterministic_count() -> None:
    queue = run_self_build_operator_queue()
    ids = [item["approval_id"] for item in queue["items"][:2]]
    run_self_build_approval_setter(ids, [])
    result = run_self_build_multi_apply()
    assert result["status"] == "APPLIED"
    assert result["applied_count"] == len(ids)


def test_post_validation_block_exists() -> None:
    queue = run_self_build_operator_queue()
    first_id = queue["items"][0]["approval_id"]
    run_self_build_approval_setter([first_id], [])
    result = run_self_build_multi_apply()
    assert "post_validation" in result
    assert {"validator", "operator_health", "invariance"}.issubset(result["post_validation"].keys())
