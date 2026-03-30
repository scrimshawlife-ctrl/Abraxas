from __future__ import annotations

import json
from pathlib import Path

from abx.federated_evidence import extract_federated_evidence


def test_extract_federated_evidence_missing_payload_is_explicit() -> None:
    evidence = extract_federated_evidence(None)
    assert evidence.evidence_present is False
    assert "promotion_attestation_missing" in evidence.blockers


def test_extract_federated_evidence_valid_markers() -> None:
    payload = {
        "federated": {
            "external_attestation_refs": ["remote://attest/1"],
            "federated_ledger_ids": ["ledger-1"],
            "remote_validation_status": "VALID",
            "remote_attestation_status": "PASS",
        }
    }
    evidence = extract_federated_evidence(payload)
    assert evidence.evidence_present is True
    assert evidence.federated_evidence_state == "PARTIAL"


def test_extract_federated_evidence_manifest_missing_is_explicit(tmp_path: Path) -> None:
    payload = {
        "federated": {
            "remote_evidence_manifest": "out/federated/missing-manifest.json",
            "external_attestation_refs": ["remote://attest/1"],
            "federated_ledger_ids": ["ledger-1"],
            "remote_validation_status": "VALID",
            "remote_attestation_status": "PASS",
        }
    }
    evidence = extract_federated_evidence(payload, base_dir=tmp_path)
    assert evidence.remote_evidence_status == "MISSING"
    assert evidence.federated_evidence_state == "PARTIAL"
    assert "remote_evidence_manifest_missing" in evidence.blockers


def test_extract_federated_evidence_manifest_valid_sets_state_valid(tmp_path: Path) -> None:
    manifest = tmp_path / "out" / "federated" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "schema": "RemoteEvidenceManifest.v1",
                "manifest_id": "fed-man-1",
                "run_id": "RUN-FED-1",
                "origin": "federation://cluster-a",
                "packets": [
                    {
                        "packet_id": "pkt-1",
                        "run_id": "RUN-FED-1",
                        "ref": "remote://pkt/1",
                        "status": "VALID",
                        "observed_at": "2026-03-30T00:00:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    payload = {
        "federated": {
            "remote_evidence_manifest": manifest.relative_to(tmp_path).as_posix(),
            "external_attestation_refs": ["remote://attest/1"],
            "federated_ledger_ids": ["ledger-1"],
            "remote_validation_status": "VALID",
            "remote_attestation_status": "PASS",
        }
    }
    evidence = extract_federated_evidence(payload, base_dir=tmp_path)
    assert evidence.remote_evidence_status == "VALID"
    assert evidence.federated_evidence_state == "VALID"
    assert evidence.remote_evidence_manifest_id == "fed-man-1"
    assert evidence.remote_evidence_packet_count == 1


def test_extract_federated_evidence_manifest_inconsistent_sets_state(tmp_path: Path) -> None:
    manifest = tmp_path / "out" / "federated" / "manifest-inconsistent.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "schema": "RemoteEvidenceManifest.v1",
                "manifest_id": "fed-man-2",
                "run_id": "RUN-FED-2",
                "origin": "federation://cluster-a",
                "packets": [
                    {
                        "packet_id": "pkt-1",
                        "run_id": "RUN-FED-2",
                        "ref": "remote://pkt/1",
                        "status": "VALID",
                        "observed_at": "2026-03-30T00:00:00+00:00",
                    },
                    {
                        "packet_id": "pkt-2",
                        "run_id": "RUN-FED-2",
                        "ref": "remote://pkt/2",
                        "status": "FAIL",
                        "observed_at": "2026-03-30T00:00:00+00:00",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    payload = {
        "federated": {
            "remote_evidence_manifest": manifest.relative_to(tmp_path).as_posix(),
            "external_attestation_refs": ["remote://attest/1"],
            "federated_ledger_ids": ["ledger-1"],
            "remote_validation_status": "VALID",
            "remote_attestation_status": "PASS",
        }
    }
    evidence = extract_federated_evidence(payload, base_dir=tmp_path)
    assert evidence.federated_evidence_state == "INCONSISTENT"
    assert evidence.federated_inconsistency is True
    assert "remote_evidence_inconsistent" in evidence.blockers
