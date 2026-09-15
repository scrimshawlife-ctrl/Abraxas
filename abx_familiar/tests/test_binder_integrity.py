from abx_familiar.binder.bind import bind_shadow
from abx_familiar.ingest.familiar_ingestion_receipt import build_familiar_ingestion_receipt
from abx_familiar.ir.evidence_pack_v0 import EvidenceItem, EvidencePack
from abx_familiar.warden.warden_pre import warden_pre


def _pack(pack_id: str = "pack_int_001") -> EvidencePack:
    return EvidencePack(
        pack_id=pack_id,
        items=[EvidenceItem(evidence_id="e1", source_type="web", url="https://example.com")],
    )


def test_mismatch_pack_hash_rejected_even_if_ward_object_says_pass():
    pack = _pack()
    receipt = build_familiar_ingestion_receipt(pack)
    ward = warden_pre(pack, receipt, report_id="pre")
    assert ward.invariance_passed is True
    broken = dict(receipt)
    broken["pack_hash"] = "0" * 64
    binding = bind_shadow(pack, broken, ward, binding_id="b")
    assert binding["status"] == "BIND_REJECTED"
    assert "pack_hash_mismatch" in binding["blockers"]


def test_clean_path_still_binds():
    pack = _pack()
    receipt = build_familiar_ingestion_receipt(pack)
    ward = warden_pre(pack, receipt, report_id="pre")
    binding = bind_shadow(pack, receipt, ward, binding_id="b")
    assert binding["status"] == "BOUND_SHADOW"
    assert binding["blockers"] == []
