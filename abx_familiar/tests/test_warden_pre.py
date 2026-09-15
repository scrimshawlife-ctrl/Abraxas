from abx_familiar.ingest.familiar_ingestion_receipt import build_familiar_ingestion_receipt
from abx_familiar.ir.evidence_pack_v0 import EvidenceItem, EvidencePack
from abx_familiar.warden.warden_pre import warden_pre


def _pack() -> EvidencePack:
    return EvidencePack(
        pack_id="pack_ward_001",
        items=[EvidenceItem(evidence_id="e1", source_type="web", url="https://example.com")],
    )


def test_warden_pre_passes_shadow_receipt():
    pack = _pack()
    receipt = build_familiar_ingestion_receipt(pack, pack_ref="memory")
    report = warden_pre(pack, receipt, report_id="ward_pre_ok")
    assert report.invariance_passed is True
    assert report.violations == []
    assert report.drift_class == "none"


def test_warden_pre_blocks_authority_leak():
    pack = _pack()
    receipt = build_familiar_ingestion_receipt(pack, pack_ref="memory")
    receipt = dict(receipt)
    receipt["authority"] = {**receipt["authority"], "execution_authority": True}
    report = warden_pre(pack, receipt, report_id="ward_pre_leak")
    assert report.invariance_passed is False
    assert "execution_authority" in report.tier_leakage_flags
    assert report.drift_class == "critical"


def test_warden_pre_blocks_missing_receipt():
    report = warden_pre(_pack(), None, report_id="ward_pre_none")
    assert report.invariance_passed is False
    assert report.not_computable is True
