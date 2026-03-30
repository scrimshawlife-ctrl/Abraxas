from __future__ import annotations

import json
from pathlib import Path

from abx.operator_projection import build_operator_projection_summary


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_operator_projection_summary_local_only_complete(tmp_path: Path) -> None:
    run_id = "RUN-PROJ-LOCAL"
    _write(tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json", {"status": "VALID", "artifactId": "ev-1"})
    _write(tmp_path / "out" / "attestation" / f"canonical_proof_{run_id}.json", {"overall_status": "PASS"})
    _write(tmp_path / "out" / "operator" / f"proof_projection_{run_id}.json", {"artifactType": "OperatorProofProjection.v1"})

    summary = build_operator_projection_summary(run_id, base_dir=tmp_path, generated_at="2026-03-30T00:00:00+00:00")

    assert summary.schema == "OperatorProjectionSummary.v1"
    assert summary.tier1_local_closure == "PASS"
    assert summary.tier2_local_promotion_state == "LOCAL_ONLY_COMPLETE"
    assert summary.tier25_federated_readiness_state == "NOT_COMPUTABLE"
    assert summary.promotion_policy_state == "BLOCKED"


def test_operator_projection_summary_federated_ready(tmp_path: Path) -> None:
    run_id = "RUN-PROJ-READY"
    _write(tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json", {"status": "VALID"})
    _write(tmp_path / "out" / "attestation" / f"canonical_proof_{run_id}.json", {"overall_status": "PASS"})
    _write(
        tmp_path / "out" / "attestation" / f"execution-attestation-{run_id}.json",
        {
            "overall_status": "PASS",
            "federated": {
                "external_attestation_refs": ["remote://attest/1"],
                "federated_ledger_ids": ["ledger-1"],
                "remote_validation_status": "VALID",
                "remote_attestation_status": "PASS",
            },
        },
    )

    summary = build_operator_projection_summary(run_id, base_dir=tmp_path, generated_at="2026-03-30T00:00:00+00:00")

    assert summary.tier2_local_promotion_state == "LOCAL_PROMOTION_READY"
    assert summary.tier25_federated_readiness_state == "FEDERATED_READY"
    assert summary.federated_evidence_present is True
    assert summary.federated_evidence_state_summary == "PARTIAL" or summary.federated_evidence_state_summary == "VALID"
    assert summary.remote_evidence_packet_count >= 0
    assert summary.promotion_policy_state == "ALLOWED"
    assert summary.promotion_policy_waived is False


def test_operator_projection_summary_federated_incomplete_when_missing_markers(tmp_path: Path) -> None:
    run_id = "RUN-PROJ-FED-MISS"
    _write(tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json", {"status": "VALID"})
    _write(tmp_path / "out" / "attestation" / f"canonical_proof_{run_id}.json", {"overall_status": "PASS"})
    _write(tmp_path / "out" / "attestation" / f"execution-attestation-{run_id}.json", {"overall_status": "PASS"})

    summary = build_operator_projection_summary(run_id, base_dir=tmp_path, generated_at="2026-03-30T00:00:00+00:00")

    assert summary.tier25_federated_readiness_state == "FEDERATED_INCOMPLETE"
    assert "missing_external_attestation_refs_and_federated_ledger_ids" in summary.federated_blockers
    assert summary.promotion_policy_state == "BLOCKED"
    assert "federated_readiness_required" in summary.promotion_policy_reason_codes


def test_operator_projection_summary_not_computable_without_local_artifacts(tmp_path: Path) -> None:
    summary = build_operator_projection_summary("RUN-PROJ-NC", base_dir=tmp_path, generated_at="2026-03-30T00:00:00+00:00")

    assert summary.tier2_local_promotion_state == "NOT_COMPUTABLE"
    assert summary.tier25_federated_readiness_state == "NOT_COMPUTABLE"
    assert summary.promotion_policy_state == "NOT_COMPUTABLE"


def test_operator_projection_summary_is_deterministic_given_fixed_inputs(tmp_path: Path) -> None:
    run_id = "RUN-PROJ-DET"
    _write(tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json", {"status": "VALID", "artifactId": "ev-det"})
    _write(tmp_path / "out" / "attestation" / f"canonical_proof_{run_id}.json", {"overall_status": "PASS"})

    a = build_operator_projection_summary(run_id, base_dir=tmp_path, generated_at="2026-03-30T00:00:00+00:00")
    b = build_operator_projection_summary(run_id, base_dir=tmp_path, generated_at="2026-03-30T00:00:00+00:00")

    assert a.to_dict() == b.to_dict()


def test_operator_projection_summary_inconsistent_federated_state(tmp_path: Path) -> None:
    run_id = "RUN-PROJ-INCONS"
    _write(tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json", {"status": "VALID"})
    _write(tmp_path / "out" / "attestation" / f"canonical_proof_{run_id}.json", {"overall_status": "PASS"})
    _write(
        tmp_path / "out" / "federated" / "manifest.json",
        {
            "schema": "RemoteEvidenceManifest.v1",
            "manifest_id": "manifest-incons",
            "run_id": run_id,
            "origin": "federation://cluster-a",
            "packets": [
                {"packet_id": "pkt-1", "run_id": run_id, "ref": "remote://pkt/1", "status": "VALID", "observed_at": "2026-03-30T00:00:00+00:00"},
                {"packet_id": "pkt-2", "run_id": run_id, "ref": "remote://pkt/2", "status": "FAIL", "observed_at": "2026-03-30T00:00:00+00:00"},
            ],
        },
    )
    _write(
        tmp_path / "out" / "attestation" / f"execution-attestation-{run_id}.json",
        {
            "overall_status": "PASS",
            "federated": {
                "external_attestation_refs": ["remote://attest/1"],
                "federated_ledger_ids": ["ledger-1"],
                "remote_validation_status": "VALID",
                "remote_attestation_status": "PASS",
                "remote_evidence_manifest": "out/federated/manifest.json",
            },
        },
    )

    summary = build_operator_projection_summary(run_id, base_dir=tmp_path, generated_at="2026-03-30T00:00:00+00:00")

    assert summary.federated_evidence_state_summary == "INCONSISTENT"
    assert summary.federated_inconsistency_flag is True
    assert summary.remote_evidence_packet_count == 2
