from __future__ import annotations

from typing import Any
import hashlib
import json

from .self_build_operator_queue import run_self_build_operator_queue


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_self_build_approval_receipt(
    approved_ids: list[str],
    rejected_ids: list[str],
    queue: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # `queue` is an injection seam for tests, so the approval-mapping logic can be
    # exercised without depending on live repo state. When omitted the live
    # operator queue is used, exactly as before.
    #
    # Why this matters: the live queue derives from the self-build chain's scan for
    # NOT_COMPUTABLE targets, and it legitimately drains to EMPTY once every target
    # has been upgraded. A test asserting a non-zero queue depth therefore asserts
    # mutable repo state rather than this function's contract -- and can never pass
    # again on a remediated repo. See docs/TEST_DEBT.md.
    if queue is None:
        queue = run_self_build_operator_queue()

    approvals = []
    for item in queue["items"]:
        approval_id = item["approval_id"]
        if approval_id in approved_ids:
            status = "APPROVED"
        elif approval_id in rejected_ids:
            status = "REJECTED"
        else:
            status = "PENDING"

        approvals.append(
            {
                "approval_id": approval_id,
                "target_path": item["target_path"],
                "status": status,
            }
        )

    payload = {
        "schema_version": "SelfBuildApprovalReceipt.v1",
        "approval_count": len(approvals),
        "approvals": sorted(approvals, key=lambda item: item["approval_id"]),
    }
    payload_hash = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return {
        **payload,
        "canonical_hash": payload_hash,
        "authority": {
            "mutation": False,
            "execution": False,
            "operator_controlled": True,
            "observe_only": True,
        },
    }
