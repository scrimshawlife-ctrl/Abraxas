"""Weave — declared attachment refs only. No rewrite."""

from __future__ import annotations

from typing import Any

from abx_familiar.ir.delivery_pack_v0 import AttachmentRef
from abx_familiar.ir.evidence_pack_v0 import EvidencePack
from abx_familiar.ir.ward_report_v0 import WardReport


def weave_shadow(
    pack: EvidencePack,
    receipt: dict[str, Any],
    ward_pre: WardReport,
    binding: dict[str, Any],
) -> list[AttachmentRef]:
    return [
        AttachmentRef(kind="evidence", ref_id=pack.hash(), meta={"pack_id": pack.pack_id}),
        AttachmentRef(kind="receipt", ref_id=str(receipt.get("receipt_hash") or "missing")),
        AttachmentRef(kind="ward_report", ref_id=ward_pre.hash(), meta={"gate": "pre"}),
        AttachmentRef(kind="binding", ref_id=str(binding.get("binding_hash") or "missing")),
    ]
