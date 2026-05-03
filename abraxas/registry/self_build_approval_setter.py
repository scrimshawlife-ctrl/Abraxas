from __future__ import annotations

from typing import Any
import json
from pathlib import Path

from .self_build_operator_queue import run_self_build_operator_queue


def run_self_build_approval_setter(
    approved_ids: list[str],
    rejected_ids: list[str],
) -> dict[str, Any]:
    queue = run_self_build_operator_queue()
    valid_ids = {item["approval_id"] for item in queue["items"]}

    errors: list[str] = []
    for approved_id in approved_ids:
        if approved_id not in valid_ids:
            errors.append(f"UNKNOWN_APPROVAL_ID:{approved_id}")

    for rejected_id in rejected_ids:
        if rejected_id not in valid_ids:
            errors.append(f"UNKNOWN_REJECTION_ID:{rejected_id}")

    overlap = set(approved_ids) & set(rejected_ids)
    if overlap:
        errors.append(f"OVERLAP_IDS:{sorted(list(overlap))}")

    if errors:
        return {
            "schema_version": "SelfBuildApprovalSetter.v1",
            "status": "INVALID_INPUT",
            "errors": sorted(errors),
            "authority": {
                "mutation": False,
                "execution": False,
                "fail_closed": True,
            },
        }

    payload = {
        "schema_version": "SelfBuildApprovalInput.v1",
        "approved_ids": sorted(approved_ids),
        "rejected_ids": sorted(rejected_ids),
    }
    out_path = Path("out/registry/self_build_approval_input.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return {
        "schema_version": "SelfBuildApprovalSetter.v1",
        "status": "VALID",
        "approved_count": len(approved_ids),
        "rejected_count": len(rejected_ids),
        "authority": {
            "mutation": False,
            "execution": False,
            "validated_write": True,
        },
    }
