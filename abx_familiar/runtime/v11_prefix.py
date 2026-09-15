"""Run the implemented spec v1.1 prefix: forage receipt → warden_pre → bind.

Weaver, Warden-post, and Herald stay closed.
"""

from __future__ import annotations

from typing import Any

from abx_familiar.binder.bind import bind_shadow
from abx_familiar.ingest.familiar_ingestion_receipt import build_familiar_ingestion_receipt
from abx_familiar.ir.evidence_pack_v0 import EvidencePack
from abx_familiar.summoner import build_v11_invocation_plan
from abx_familiar.warden.warden_pre import warden_pre


def run_v11_prefix(pack: EvidencePack, *,
    pack_ref: str = "",
    run_id: str = "v11_prefix",
) -> dict[str, Any]:
    plan = build_v11_invocation_plan(plan_id=f"{run_id}_plan")
    receipt = build_familiar_ingestion_receipt(pack, pack_ref=pack_ref)
    ward = warden_pre(pack, receipt, report_id=f"{run_id}_ward_pre")
    binding = bind_shadow(pack, receipt, ward, binding_id=f"{run_id}_bind")
    return {
        "coupling": "spec_v1.1",
        "plan_id": plan.plan_id,
        "plan_hash": plan.hash(),
        "receipt": receipt,
        "ward_pre": ward.to_payload(),
        "binding": binding,
        "closed": ["weave", "ward_post", "herald"],
    }
