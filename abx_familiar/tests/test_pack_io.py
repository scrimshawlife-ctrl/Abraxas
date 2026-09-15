from abx_familiar.ingest.familiar_ingestion_receipt import (
    build_familiar_ingestion_receipt_from_path,
)
from abx_familiar.ingest.pack_io import load_evidence_pack


def test_fixture_loads_and_receipts():
    path = "fixtures/familiar/pack_companion_dryrun_2026-09-15.v0.json"
    pack = load_evidence_pack(path)
    assert pack.pack_id == "pack_companion_dryrun_2026-09-15"
    assert len(pack.items) == 3
    receipt = build_familiar_ingestion_receipt_from_path(path)
    assert receipt["status"] == "INGESTED_SHADOW"
    assert receipt["pack_id"] == pack.pack_id
    assert receipt["pack_hash"] == pack.hash()
