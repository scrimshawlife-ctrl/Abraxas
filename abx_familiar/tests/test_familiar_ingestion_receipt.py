from abx_familiar.ingest.familiar_ingestion_receipt import build_familiar_ingestion_receipt
from abx_familiar.ir.evidence_pack_v0 import EvidenceItem, EvidencePack


def test_no_input_is_shadow_not_computable():
    receipt = build_familiar_ingestion_receipt(None)
    assert receipt["status"] == "NO_INPUT"
    assert receipt["lane"] == "SHADOW"
    assert receipt["authority"]["execution_authority"] is False
    assert receipt["claim_count"] == 0


def test_valid_pack_ingests_shadow():
    pack = EvidencePack(
        pack_id="pack_test_001",
        items=[
            EvidenceItem(
                evidence_id="ev1",
                source_type="web",
                url="https://example.com/a",
            )
        ],
        collection_context={"topic": "test", "intent": "forage"},
    )
    receipt = build_familiar_ingestion_receipt(pack, pack_ref="memory")
    assert receipt["status"] == "INGESTED_SHADOW"
    assert receipt["validation_status"] == "PASS"
    assert receipt["source_count"] == 1
    assert receipt["observed_claim_count"] == 0
    assert receipt["commercial_claims_blocked"] is True
    assert receipt["schema_version"] == "FamiliarIngestionReceipt.v0"
    assert len(receipt["receipt_hash"]) == 64
