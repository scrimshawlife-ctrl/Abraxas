from __future__ import annotations

from typing import Any
import hashlib
import json
from pathlib import Path


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _scan_not_computable() -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    base = Path("out")
    if not base.exists():
        return targets

    for file in base.rglob("*.json"):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            if data.get("status") == "NOT_COMPUTABLE":
                targets.append(
                    {
                        "path": str(file),
                        "schema_version": data.get("schema_version"),
                        "reason": data.get("reason", "UNKNOWN"),
                    }
                )
        except Exception:
            continue

    return sorted(targets, key=lambda item: item["path"])


def run_self_build_proposal() -> dict[str, Any]:
    targets = _scan_not_computable()
    proposals = []
    for target in targets:
        proposals.append(
            {
                "target_path": target["path"],
                "current_state": "NOT_COMPUTABLE",
                "proposed_transition": "COMPUTABLE",
                "strategy": "IMPLEMENT_MINIMAL_LOGIC",
                "constraints": [
                    "must_preserve_schema",
                    "must_preserve_authority_flags",
                    "must_not_enable_mutation",
                    "must_not_enable_promotion",
                ],
            }
        )

    payload = {
        "schema_version": "SelfBuildProposal.v1",
        "proposal_count": len(proposals),
        "proposals": proposals,
    }
    payload_hash = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return {
        **payload,
        "canonical_hash": payload_hash,
        "authority": {
            "mutation": False,
            "promotion": False,
            "execution": False,
            "observe_only": True,
        },
    }
