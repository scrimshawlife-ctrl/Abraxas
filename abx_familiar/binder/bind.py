"""Binder — spec v1.1 evidence gate.

Seals pack_hash + receipt_hash + ward_pre hash.
Does not weave, infer, or grant authority.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from abx_familiar.ir.evidence_pack_v0 import EvidencePack
from abx_familiar.ir.ward_report_v0 import WardReport

SCHEMA = "FamiliarBinding.v0"


def _hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def bind_shadow(
    pack: EvidencePack,
    receipt: dict[str, Any],
    ward_pre: WardReport,
    *,
    binding_id: str = "bind_unspecified",
) -> dict[str, Any]:
    if not ward_pre.invariance_passed:
        body = {
            "schema_version": SCHEMA,
            "binding_id": binding_id,
            "status": "BIND_REJECTED",
            "lane": "SHADOW",
            "advisory_only": True,
            "authority": {
                "execution_authority": False,
                "promotion_authorized": False,
                "forecast_routing_authorized": False,
                "canon_mutation_allowed": False,
            },
            "pack_id": pack.pack_id,
            "pack_hash": pack.hash() if pack else "",
            "receipt_id": receipt.get("receipt_id", ""),
            "receipt_hash": receipt.get("receipt_hash", ""),
            "ward_pre_id": ward_pre.report_id,
            "ward_pre_hash": ward_pre.hash(),
            "blockers": ["ward_pre_failed"],
        }
        body["binding_hash"] = _hash(body)
        return body

    body = {
        "schema_version": SCHEMA,
        "binding_id": binding_id,
        "status": "BOUND_SHADOW",
        "lane": "SHADOW",
        "advisory_only": True,
        "authority": {
            "execution_authority": False,
            "promotion_authorized": False,
            "forecast_routing_authorized": False,
            "canon_mutation_allowed": False,
        },
        "pack_id": pack.pack_id,
        "pack_hash": pack.hash(),
        "receipt_id": str(receipt.get("receipt_id", "")),
        "receipt_hash": str(receipt.get("receipt_hash", "")),
        "ward_pre_id": ward_pre.report_id,
        "ward_pre_hash": ward_pre.hash(),
        "blockers": [],
    }
    body["binding_hash"] = _hash({k: v for k, v in body.items() if k != "binding_hash"})
    return body
