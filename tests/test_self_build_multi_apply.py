from __future__ import annotations

from abraxas.registry.self_build_approval_setter import run_self_build_approval_setter
from abraxas.registry.self_build_multi_apply import run_self_build_multi_apply


def test_no_approvals_returns_no_approved_items() -> None:
    run_self_build_approval_setter([], [])
    result = run_self_build_multi_apply()
    assert result["status"] == "NO_APPROVED_ITEMS"


# Synthetic queue for hermetic tests (using the injection seam).
# These tests no longer depend on live NOT_COMPUTABLE targets in the tree.
_SYNTH_QUEUE = {
    "items": [
        {
            "approval_id": "approval-0001",
            "target_path": "out/test/target1.json",
            "proposed_action": "upgrade",
            "expected_result": {"status": "COMPUTABLE"},
            "approval_status": "PENDING_OPERATOR_APPROVAL",
            "safety_verified": True,
            "green_state_preserved_predicted": True,
            "validation_commands": [],
            "rollback": "NOT_AVAILABLE",
        },
        {
            "approval_id": "approval-0002",
            "target_path": "out/test/target2.json",
            "proposed_action": "upgrade",
            "expected_result": {"status": "COMPUTABLE"},
            "approval_status": "PENDING_OPERATOR_APPROVAL",
            "safety_verified": True,
            "green_state_preserved_predicted": True,
            "validation_commands": [],
            "rollback": "NOT_AVAILABLE",
        },
    ],
    "queue_count": 2,
}


def test_duplicate_target_fails_closed() -> None:
    first_id = _SYNTH_QUEUE["items"][0]["approval_id"]
    run_self_build_approval_setter([first_id, first_id], [], queue=_SYNTH_QUEUE)
    result = run_self_build_multi_apply(queue=_SYNTH_QUEUE)
    assert result["status"] == "NOT_COMPUTABLE"


def test_one_approved_applies_one_target() -> None:
    first_id = _SYNTH_QUEUE["items"][0]["approval_id"]
    run_self_build_approval_setter([first_id], [], queue=_SYNTH_QUEUE)
    result = run_self_build_multi_apply(queue=_SYNTH_QUEUE)
    assert result["status"] == "APPLIED"
    assert result["applied_count"] == 1


def test_multi_approved_ids_apply_deterministic_count() -> None:
    ids = [item["approval_id"] for item in _SYNTH_QUEUE["items"][:2]]
    run_self_build_approval_setter(ids, [], queue=_SYNTH_QUEUE)
    result = run_self_build_multi_apply(queue=_SYNTH_QUEUE)
    assert result["status"] == "APPLIED"
    assert result["applied_count"] == len(ids)


def test_post_validation_block_exists() -> None:
    first_id = _SYNTH_QUEUE["items"][0]["approval_id"]
    run_self_build_approval_setter([first_id], [], queue=_SYNTH_QUEUE)
    result = run_self_build_multi_apply(queue=_SYNTH_QUEUE)
    assert "post_validation" in result
    assert {"validator", "operator_health", "invariance"}.issubset(result["post_validation"].keys())
