from abx_familiar.binder.bind import bind_shadow
from abx_familiar.ingest.familiar_ingestion_receipt import build_familiar_ingestion_receipt
from abx_familiar.ir.evidence_pack_v0 import EvidenceItem, EvidencePack
from abx_familiar.ledger.in_memory_store import InMemoryAppendOnlyStore
from abx_familiar.runtime.v11_prefix import run_v11_prefix
from abx_familiar.summoner import SEQUENCE, build_v11_invocation_plan
from abx_familiar.warden.warden_pre import warden_pre


def _pack() -> EvidencePack:
    return EvidencePack(
        pack_id="pack_bind_001",
        items=[EvidenceItem(evidence_id="e1", source_type="web", url="https://example.com")],
    )


def test_v11_plan_declares_ward_pre_before_forage():
    plan = build_v11_invocation_plan()
    ids = [e.before_invocation_id + "->" + e.after_invocation_id for e in plan.dependency_edges]
    assert "ward_pre->forage" in ids
    assert "forage->bind" in ids
    assert "weave->ward_post" in ids
    assert SEQUENCE[1][0] == "ward_pre"
    assert all(not inv.not_computable for inv in plan.rune_invocations)


def test_bind_rejects_failed_ward():
    pack = _pack()
    receipt = build_familiar_ingestion_receipt(pack)
    receipt = dict(receipt)
    receipt["authority"] = {**receipt["authority"], "execution_authority": True}
    ward = warden_pre(pack, receipt, report_id="w")
    binding = bind_shadow(pack, receipt, ward, binding_id="b")
    assert binding["status"] == "BIND_REJECTED"


def test_prefix_runs_full_v11_tail():
    store = InMemoryAppendOnlyStore()
    out = run_v11_prefix(_pack(), run_id="t1", ledger_store=store)
    assert out["binding"]["status"] == "BOUND_SHADOW"
    assert out["ward_pre"]["invariance_passed"] is True
    assert out["ward_post"]["invariance_passed"] is True
    assert out["ledger_entry"]["not_computable"] is False
    assert out["ledger_entry"]["output_hash"] != out["binding"]["binding_hash"]
    assert out["herald"]["mode"] == "Analyst"
    assert out["herald"]["not_computable"] is False
    assert out["closed"] == []
    kinds = {row["kind"] for row in out["weave"]}
    assert kinds == {"evidence", "receipt", "ward_report", "binding"}
