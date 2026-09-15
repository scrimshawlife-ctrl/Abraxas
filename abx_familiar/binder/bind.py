"""Binder — spec v1.1 evidence gate.

Seals pack_hash + receipt_hash + ward_pre hash.
Also checks pack_id, pack_hash, and receipt status. Does not infer.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from abx_familiar.ir.evidence_pack_v0 import EvidencePack
from abx_familiar.ir.ward_report_v0 import WardReport

SCHEMA = "FamiliarBinding.v0"
AUTHORITY = {
    "execution_authority": False,
    "promotion_authorized": False,
    "forecast_routing_authorized": False,
    "canon_mutation_allowed": False,
}


def _hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _body(
    *,
    binding_id: str,
    status: str,
    pack: EvidencePack,
    receipt: dict[str, Any],
    ward_pre: WardReport,
    blockers: list[str],
) -> dict[str, Any]:
    pack_hash = pack.hash()
    raw = {
        "schema_version": SCHEMA,
        "binding_id": binding_id,
        "status": status,
        "lane": "SHADOW",
        "advisory_only": True,
        "authority": dict(AUTHORITY),
        "pack_id": pack.pack_id,
        "pack_hash": pack_hash,
        "receipt_id": str(receipt.get("receipt_id", "")),
        "receipt_hash": str(receipt.get("receipt_hash", "")),
        "ward_pre_id": ward_pre.report_id,
        "ward_pre_hash": ward_pre.hash(),
        "blockers": list(blockers),
    }
    raw["binding_hash"] = _hash(raw)
    return raw


def bind_shadow(
    pack: EvidencePack,
    receipt: dict[str, Any],
    ward_pre: WardReport,
    *,
    binding_id: str = "bind_unspecified",
) -> dict[str, Any]:
    blockers: list[str] = []
    if not ward_pre.invariance_passed:
        blockers.append("ward_pre_failed")
    if receipt.get("pack_id") not in ("", None) and receipt.get("pack_id") != pack.pack_id:
        blockers.append("pack_id_mismatch")
    if receipt.get("pack_hash") and receipt.get("pack_hash") != pack.hash():
        blockers.append("pack_hash_mismatch")
    if receipt.get("status") != "INGESTED_SHADOW":
        blockers.append("receipt_not_ingested_shadow")
    if not receipt.get("receipt_hash"):
        blockers.append("missing_receipt_hash")

    status = "BIND_REJECTED" if blockers else "BOUND_SHADOW"
    return _body(
        binding_id=binding_id,
        status=status,
        pack=pack,
        receipt=receipt,
        ward_pre=ward_pre,
        blockers=blockers,
    )
