from abx_familiar.ingest.familiar_ingestion_receipt import build_familiar_ingestion_receipt
from abx_familiar.ir.evidence_pack_v0 import EvidenceItem, EvidencePack
from abx_familiar.runtime.keep_output import compute_keep_output_hash
from abx_familiar.runtime.v11_prefix import run_v11_prefix
from abx_familiar.warden.warden_post import warden_post
from abx_familiar.warden.warden_pre import warden_pre
from abx_familiar.binder.bind import bind_shadow
from abx_familiar.weaver.weave import weave_shadow


def _pack() -> EvidencePack:
    return EvidencePack(
        pack_id="pack_keep_hash_001",
        items=[EvidenceItem(evidence_id="e1", source_type="web", url="https://example.com")],
    )


def test_keep_output_hash_is_not_binding_hash():
    pack = _pack()
    receipt = build_familiar_ingestion_receipt(pack)
    ward = warden_pre(pack, receipt, report_id="pre")
    binding = bind_shadow(pack, receipt, ward, binding_id="b")
    weave = weave_shadow(pack, receipt, ward, binding)
    post = warden_post(binding, weave, report_id="post")
    digest = compute_keep_output_hash(binding, weave, post)
    assert len(digest) == 64
    assert digest != binding["binding_hash"]


def test_prefix_stores_keep_output_v1():
    out = run_v11_prefix(_pack(), run_id="kh1")
    assert out["ledger_entry"]["meta"]["output_hash_method"] == "keep_output.v1"
    assert out["ledger_entry"]["output_hash"] != out["binding"]["binding_hash"]
    assert len(out["ledger_entry"]["output_hash"]) == 64
