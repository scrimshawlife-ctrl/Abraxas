import json
from pathlib import Path

from abx_familiar.ingest.familiar_ingestion_receipt import (
    build_familiar_ingestion_receipt,
)
from abx_familiar.ingest.pack_io import load_evidence_pack
from abx_familiar.ingest.project_v2_pack import project_v2_pack_dict
from abx_familiar.warden.warden_pre import warden_pre


def _v2_pack() -> dict:
    return {
        "schema_version": "EvidencePack.v0",
        "pack_id": "pack_project_fixture_001",
        "topic": "adapter fixture",
        "intent": "tech",
        "must_answer": ["does projection preserve sources?"],
        "sources": [
            {
                "source_id": "S001",
                "url_or_path": "https://example.com/a",
                "title": "Example A",
                "publisher": "example",
                "source_class": "primary",
                "excerpt": "excerpt",
            }
        ],
        "claims": [
            {
                "claim_id": "C001",
                "text": "Example A exists.",
                "register": "OBSERVED",
                "source_ids": ["S001"],
            }
        ],
        "authority": {
            "execution_authority": False,
            "promotion_authorized": False,
            "forecast_routing_authorized": False,
            "canon_mutation_allowed": False,
        },
        "provenance": {
            "producer_system": "OPERATOR",
            "skill_id": "abx-familiar-signal-forager",
            "tool_trace_summary": "unit fixture",
        },
    }


def test_project_v2_pack_builds_items_and_sidecar():
    local, sidecar = project_v2_pack_dict(_v2_pack())
    assert local.pack_id == "pack_project_fixture_001"
    assert len(local.items) == 2
    assert local.collection_context["topic"] == "adapter fixture"
    assert sidecar["claim_count"] == 1
    assert sidecar["claims"][0]["truth_assignment"] is False
    receipt = build_familiar_ingestion_receipt(local, pack_ref="memory")
    assert receipt["status"] == "INGESTED_SHADOW"
    assert receipt["claim_count"] == 0
    assert receipt["source_count"] == 2
    assert receipt["topic"] == "adapter fixture"


def test_pack_io_projects_v2_file(tmp_path: Path):
    path = tmp_path / "v2.json"
    path.write_text(json.dumps(_v2_pack()), encoding="utf-8")
    pack = load_evidence_pack(path)
    assert len(pack.items) == 2
    assert pack.items[0].evidence_id == "src_S001"


def test_warden_pre_warns_not_fails_on_density_gate():
    local, _ = project_v2_pack_dict(_v2_pack())
    receipt = build_familiar_ingestion_receipt(local, pack_ref="memory")
    receipt = dict(receipt)
    receipt["commercial_claims_blocked"] = False
    report = warden_pre(local, receipt, report_id="ward_pre_density")
    assert report.invariance_passed is True
    assert report.drift_class == "benign"
    assert any(f.code == "COMMERCIAL_UNBLOCKED" for f in report.warnings)
    assert all(f.code != "COMMERCIAL_UNBLOCKED" for f in report.violations)
