from __future__ import annotations

from abraxas.registry.self_build_approval_setter import run_self_build_approval_setter
from abraxas.registry.self_build_controlled_apply import run_self_build_controlled_apply

# Synthetic queue for hermetic tests (duplicated for this module).
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
    ],
    "queue_count": 1,
}


def test_apply_fails_closed() -> None:
    run_self_build_approval_setter([], [])
    result = run_self_build_controlled_apply()
    assert result["status"] == "NO_APPROVED_ITEMS"
    assert result["applied_count"] == 0


def test_apply_one_item() -> None:
    first_id = _SYNTH_QUEUE["items"][0]["approval_id"]
    run_self_build_approval_setter([first_id], [], queue=_SYNTH_QUEUE)
    result = run_self_build_controlled_apply(queue=_SYNTH_QUEUE)
    assert result["status"] == "APPLIED"
    assert result["applied_count"] == 1
