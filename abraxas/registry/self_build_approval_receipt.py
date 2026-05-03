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
) -> dict[str, Any]:
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
