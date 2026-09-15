"""Spec v1.1 prefix: receipt → warden_pre → bind → weave → warden_post → keep → herald."""

from __future__ import annotations

from typing import Any

from abx_familiar.binder.bind import bind_shadow
from abx_familiar.herald import herald_pointer
from abx_familiar.ingest.familiar_ingestion_receipt import build_familiar_ingestion_receipt
from abx_familiar.ir.evidence_pack_v0 import EvidencePack
from abx_familiar.ledger.in_memory_store import InMemoryAppendOnlyStore
from abx_familiar.runtime.familiar_runtime import Keeper
from abx_familiar.summoner import build_v11_invocation_plan
from abx_familiar.warden.warden_post import warden_post
from abx_familiar.warden.warden_pre import warden_pre
from abx_familiar.weaver.weave import weave_shadow


def run_v11_prefix(
    pack: EvidencePack,
    *,
    pack_ref: str = "",
    run_id: str = "v11_prefix",
    ledger_store: InMemoryAppendOnlyStore | None = None,
) -> dict[str, Any]:
    plan = build_v11_invocation_plan(plan_id=f"{run_id}_plan")
    receipt = build_familiar_ingestion_receipt(pack, pack_ref=pack_ref)
    ward = warden_pre(pack, receipt, report_id=f"{run_id}_ward_pre")
    binding = bind_shadow(pack, receipt, ward, binding_id=f"{run_id}_bind")
    weave = weave_shadow(pack, receipt, ward, binding)
    ward_post = warden_post(binding, weave, report_id=f"{run_id}_ward_post")

    keeper = Keeper()
    bound = binding.get("status") == "BOUND_SHADOW" and ward_post.invariance_passed
    entry = keeper.run(
        run_id=run_id,
        input_hash=pack.hash(),
        task_graph_hash=plan.hash(),
        invocation_plan_hash=plan.hash(),
        output_hash=binding.get("binding_hash") if bound else None,
        not_computable=not bound,
        missing_fields=[] if bound else ["ward_post_or_binding"],
        meta={
            "coupling": "spec_v1.1",
            "skipped_gates": [],
            "binding_status": binding.get("status"),
            "ward_post_passed": ward_post.invariance_passed,
        },
    )
    if ledger_store is not None:
        ledger_store.append(entry)

    delivery = herald_pointer(run_id, binding, entry, weave)
    return {
        "coupling": "spec_v1.1",
        "plan_id": plan.plan_id,
        "plan_hash": plan.hash(),
        "receipt": receipt,
        "ward_pre": ward.to_payload(),
        "binding": binding,
        "weave": [a.to_payload() for a in weave],
        "ward_post": ward_post.to_payload(),
        "ledger_entry": entry.to_payload(),
        "herald": delivery.to_payload(),
        "closed": [],
    }
