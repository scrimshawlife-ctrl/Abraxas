from abx_familiar.binder.bind import bind_shadow
from abx_familiar.ingest.familiar_ingestion_receipt import build_familiar_ingestion_receipt
from abx_familiar.ir.delivery_pack_v0 import AttachmentRef
from abx_familiar.ir.evidence_pack_v0 import EvidenceItem, EvidencePack
from abx_familiar.warden.warden_post import warden_post
from abx_familiar.warden.warden_pre import warden_pre
from abx_familiar.weaver.weave import weave_shadow


def _pack() -> EvidencePack:
    return EvidencePack(
        pack_id="pack_wp_001",
        items=[EvidenceItem(evidence_id="e1", source_type="web", url="https://example.com")],
    )


def test_clean_weave_passes():
    pack = _pack()
    receipt = build_familiar_ingestion_receipt(pack)
    ward = warden_pre(pack, receipt, report_id="pre")
    binding = bind_shadow(pack, receipt, ward, binding_id="b")
    weave = weave_shadow(pack, receipt, ward, binding)
    post = warden_post(binding, weave, report_id="post")
    assert post.invariance_passed is True


def test_missing_ref_fails():
    pack = _pack()
    receipt = build_familiar_ingestion_receipt(pack)
    ward = warden_pre(pack, receipt, report_id="pre")
    binding = bind_shadow(pack, receipt, ward, binding_id="b")
    bad = [
        AttachmentRef(kind="evidence", ref_id="missing"),
        AttachmentRef(kind="receipt", ref_id="a" * 64),
        AttachmentRef(kind="ward_report", ref_id="b" * 64),
        AttachmentRef(kind="binding", ref_id="c" * 64),
    ]
    post = warden_post(binding, bad, report_id="post")
    assert post.invariance_passed is False
    assert any(v.code == "WEAVE_REF_INVALID" for v in post.violations)
