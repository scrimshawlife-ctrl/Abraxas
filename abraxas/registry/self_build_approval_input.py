from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_self_build_approval_input(
    path: str | Path = "out/registry/self_build_approval_input.latest.json",
) -> dict[str, Any]:
    input_path = Path(path)
    if not input_path.exists():
        payload = {
            "schema_version": "SelfBuildApprovalInput.v1",
            "approved_ids": [],
            "rejected_ids": [],
        }
        payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return payload

    raw = json.loads(input_path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "SelfBuildApprovalInput.v1":
        raise ValueError("Invalid approval input schema_version")

    approved_ids = raw.get("approved_ids")
    rejected_ids = raw.get("rejected_ids")
    if not isinstance(approved_ids, list) or not isinstance(rejected_ids, list):
        raise ValueError("approved_ids and rejected_ids must be lists")

    payload = {
        "schema_version": "SelfBuildApprovalInput.v1",
        "approved_ids": approved_ids,
        "rejected_ids": rejected_ids,
    }
    payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return payload
