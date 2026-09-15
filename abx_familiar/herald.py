"""Herald — pointer to keep entry. No promotion copy."""

from __future__ import annotations

from typing import Any

from abx_familiar.ir.continuity_ledger_v0 import ContinuityLedgerEntry
from abx_familiar.ir.delivery_pack_v0 import AttachmentRef, DeliveryPack


def herald_pointer(
    run_id: str,
    binding: dict[str, Any],
    entry: ContinuityLedgerEntry,
    attachments: list[AttachmentRef],
) -> DeliveryPack:
    extra = list(attachments) + [
        AttachmentRef(kind="ledger_entry", ref_id=entry.hash(), meta={"run_id": run_id}),
    ]
    text = (
        f"SHADOW keep {run_id} binding={binding.get('binding_hash', '')} "
        f"status={binding.get('status', '')}"
    )
    bound = binding.get("status") == "BOUND_SHADOW"
    return DeliveryPack(
        delivery_id=f"herald_{run_id}",
        mode="Analyst",
        tier_scope="Academic",
        rendered_output=text,
        attachments=extra,
        provenance_manifest={
            "coupling": "spec_v1.1",
            "lane": "SHADOW",
            "advisory_only": True,
        },
        not_computable=not bound,
        missing_fields=[] if bound else ["binding"],
    )
