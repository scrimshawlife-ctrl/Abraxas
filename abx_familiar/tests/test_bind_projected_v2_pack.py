from abx_familiar.binder.bind import bind_shadow
from abx_familiar.ingest.familiar_ingestion_receipt import (
    build_familiar_ingestion_receipt,
)
from abx_familiar.ingest.pack_io import load_evidence_pack
from abx_familiar.warden.warden_pre import warden_pre

FIXTURE = "fixtures/familiar/pack_h_forage_min.v0.json"


def test_projected_v2_pack_binds_shadow():
    pack = load_evidence_pack(FIXTURE)
    assert pack.pack_id == "pack_h_forage_min_2026-09-15"
    assert len(pack.items) == 2
    receipt = build_familiar_ingestion_receipt(pack, pack_ref=FIXTURE)
    assert receipt["status"] == "INGESTED_SHADOW"
    assert receipt["claim_count"] == 0
    ward = warden_pre(pack, receipt, report_id="ward_pre_h_forage_min")
    assert ward.invariance_passed is True
    binding = bind_shadow(pack, receipt, ward, binding_id="bind_h_forage_min")
    assert binding["status"] == "BOUND_SHADOW"
    assert binding["blockers"] == []
    assert binding["authority"]["execution_authority"] is False
    assert binding["lane"] == "SHADOW"
