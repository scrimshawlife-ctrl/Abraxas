from abx_familiar.binder.bind import bind_shadow
from abx_familiar.binder.schema import validate_binding
from abx_familiar.ingest.familiar_ingestion_receipt import build_familiar_ingestion_receipt
from abx_familiar.ir.evidence_pack_v0 import EvidenceItem, EvidencePack
from abx_familiar.warden.warden_pre import warden_pre


def _pack() -> EvidencePack:
    return EvidencePack(
        pack_id="pack_schema_001",
        items=[EvidenceItem(evidence_id="e1", source_type="web", url="https://example.com")],
    )


def test_bound_and_rejected_match_schema():
    pack = _pack()
    receipt = build_familiar_ingestion_receipt(pack)
    ward = warden_pre(pack, receipt, report_id="pre")
    ok = bind_shadow(pack, receipt, ward, binding_id="ok")
    assert validate_binding(ok) == []
    assert ok["status"] == "BOUND_SHADOW"

    broken = dict(receipt)
    broken["pack_hash"] = "0" * 64
    bad = bind_shadow(pack, broken, ward, binding_id="bad")
    assert bad["status"] == "BIND_REJECTED"
    assert validate_binding(bad) == []
