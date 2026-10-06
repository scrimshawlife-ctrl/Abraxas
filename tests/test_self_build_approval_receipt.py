from __future__ import annotations

from abraxas.registry.self_build_approval_receipt import run_self_build_approval_receipt
from abraxas.registry.self_build_operator_queue import run_self_build_operator_queue


def _queue(*approval_ids: str) -> dict:
    return {
        "schema_version": "SelfBuildOperatorQueue.v1",
        "queue_count": len(approval_ids),
        "items": [
            {"approval_id": aid, "target_path": f"out/{aid}.json"} for aid in approval_ids
        ],
    }


def test_approval_receipt_maps_operator_decisions() -> None:
    """The receipt maps approved/rejected ids onto queue items; everything else is PENDING.

    This is the function's actual contract, and it is hermetic: the queue is injected
    rather than read from the repo, so the assertions do not depend on whether the
    self-build pipeline currently has work queued.
    """
    result = run_self_build_approval_receipt(
        ["approval-bbb"],
        ["approval-ccc"],
        queue=_queue("approval-aaa", "approval-bbb", "approval-ccc"),
    )

    assert result["schema_version"] == "SelfBuildApprovalReceipt.v1"
    assert result["approval_count"] == 3
    assert {a["approval_id"]: a["status"] for a in result["approvals"]} == {
        "approval-aaa": "PENDING",
        "approval-bbb": "APPROVED",
        "approval-ccc": "REJECTED",
    }

    # Approvals are emitted sorted by approval_id, so the receipt is canonical.
    ids = [a["approval_id"] for a in result["approvals"]]
    assert ids == sorted(ids)

    # target_path is carried through from the queue item.
    assert {a["target_path"] for a in result["approvals"]} == {
        "out/approval-aaa.json",
        "out/approval-bbb.json",
        "out/approval-ccc.json",
    }


def test_approval_receipt_is_deterministic_and_observe_only() -> None:
    q = _queue("approval-aaa", "approval-bbb")

    first = run_self_build_approval_receipt(["approval-aaa"], [], queue=q)
    second = run_self_build_approval_receipt(["approval-aaa"], [], queue=q)

    assert first["canonical_hash"] == second["canonical_hash"]
    assert first == second

    # The receipt records decisions; it never authorises mutation or execution.
    assert first["authority"] == {
        "mutation": False,
        "execution": False,
        "operator_controlled": True,
        "observe_only": True,
    }


def test_approval_receipt_mirrors_the_live_queue() -> None:
    """The default path still reads the live queue, and mirrors it exactly.

    Asserts the MIRROR property rather than a non-zero depth: the live queue derives
    from the self-build chain's scan for NOT_COMPUTABLE targets and legitimately
    drains to empty once every target has been upgraded. Pinning `>= 1` here asserted
    mutable repo state, not this contract, and went permanently red on a remediated
    repo (docs/TEST_DEBT.md, self-build cleaned-chain cluster).
    """
    queue = run_self_build_operator_queue()
    result = run_self_build_approval_receipt([], [])

    assert result["approval_count"] == len(queue["items"])
    assert len(result["approvals"]) == result["approval_count"]

    # With no decisions supplied, nothing may be reported as approved or rejected.
    assert all(a["status"] == "PENDING" for a in result["approvals"])
