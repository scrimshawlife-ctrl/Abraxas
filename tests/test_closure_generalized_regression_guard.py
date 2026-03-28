from __future__ import annotations

import json
from pathlib import Path

from scripts.run_closure_generalized_attestation import build_attestation
from scripts.run_closure_scope_classification import build_scope_classification


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_scope_classification_reports_generalized_confirmed_with_non_probe_evidence(tmp_path: Path) -> None:
    audit_path = tmp_path / "artifacts_seal/audits/closure_readiness/closure_readiness.audit.v1.json"
    _write_json(
        audit_path,
        {
            "schema_version": "aal.closure_readiness.audit.v1",
            "audit_scope": "compliance_probe + execution_validator proof-chain surfaces",
            "classifications": {
                "proof_chain_continuity_emit_ledger_validate": {"status": "MISSING"},
                "correlation_pointer_sufficiency": {"status": "MISSING"},
                "promotion_relevant_evidence_sufficiency": {"status": "MISSING"},
            },
        },
    )

    _write_json(
        tmp_path / "out/validators/execution-validation-run.generalized_coverage.guard.v1.json",
        {
            "runId": "run.generalized_coverage.guard.v1",
            "validatedArtifacts": ["art.guard.v1"],
            "correlation": {
                "ledgerIds": ["ledger.guard.v1"],
                "pointers": ["out/ledger/generalized_coverage_linkage.jsonl:1"],
            },
        },
    )

    classified = build_scope_classification(base_dir=tmp_path, audit_path=audit_path)

    assert classified["summary_status"] == "GENERALIZED_CONFIRMED"
    assert classified["categories"]["GENERALIZED_CONFIRMED"]["status"] == "SATISFIED"
    assert "run.generalized_coverage.guard.v1" in classified["categories"]["GENERALIZED_CONFIRMED"]["evidence"]


def test_attestation_confirms_generalized_milestone_from_scope_and_validator_chain(tmp_path: Path) -> None:
    readiness_path = tmp_path / "artifacts_seal/audits/closure_readiness/closure_readiness.audit.v1.json"
    remediation_path = tmp_path / "artifacts_seal/audits/closure_readiness/closure_remediation_order.v1.json"
    scope_path = tmp_path / "artifacts_seal/audits/closure_readiness/closure_scope_classification.v1.json"
    validator_path = tmp_path / "out/validators/execution-validation-run.generalized_coverage.guard.v1.json"
    run_artifact_path = tmp_path / "artifacts_seal/runs/generalized_coverage/run.generalized_coverage.guard.v1.artifact.json"
    run_surface_path = tmp_path / "artifacts_seal/runs/generalized_coverage/run.generalized_coverage.guard.v1.validator_surface.json"
    ledger_path = tmp_path / "out/ledger/generalized_coverage_linkage.jsonl"

    _write_json(
        readiness_path,
        {
            "schema_version": "aal.closure_readiness.audit.v1",
            "classifications": {"proof_chain_continuity_emit_ledger_validate": {"status": "MISSING"}},
        },
    )
    _write_json(remediation_path, {"ordered_patch_list": ["PATCH.CLOSURE.004"]})
    _write_json(
        scope_path,
        {
            "summary_status": "GENERALIZED_CONFIRMED",
            "categories": {
                "GENERALIZED_CONFIRMED": {
                    "status": "SATISFIED",
                    "reason": "non-probe evidence present",
                    "evidence": ["run.generalized_coverage.guard.v1"],
                }
            },
        },
    )
    _write_json(
        validator_path,
        {
            "runId": "run.generalized_coverage.guard.v1",
            "validatedArtifacts": ["art.guard.v1"],
            "correlation": {
                "ledgerIds": ["ledger.guard.v1"],
                "pointers": ["out/ledger/generalized_coverage_linkage.jsonl:1"],
            },
        },
    )
    _write_json(
        run_artifact_path,
        {
            "run_id": "run.generalized_coverage.guard.v1",
            "artifact_id": "art.guard.v1",
            "rune_id": "RUNE.SCAN",
            "timestamp": "2026-03-28T00:00:00Z",
            "ledger_record_ids": ["ledger.guard.v1"],
            "ledger_artifact_ids": ["art.guard.v1"],
            "correlation_pointers": [
                {
                    "type": "generalized_ledger_record",
                    "value": "out/ledger/generalized_coverage_linkage.jsonl#ledger.guard.v1",
                    "status": "PRESENT",
                    "reason": "DETERMINISTIC_GENERALIZED_COVERAGE",
                }
            ],
        },
    )
    _write_json(run_surface_path, {"run_id": "run.generalized_coverage.guard.v1", "validator_surface_status": "SURFACED_TO_VALIDATOR_OUTPUT"})
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        '{"run_id":"run.generalized_coverage.guard.v1","record_id":"ledger.guard.v1","artifact_id":"art.guard.v1"}\n',
        encoding="utf-8",
    )

    attestation = build_attestation(
        readiness_path=readiness_path,
        remediation_path=remediation_path,
        scope_path=scope_path,
        validator_path=validator_path,
        run_artifact_path=run_artifact_path,
        run_surface_path=run_surface_path,
        ledger_path=ledger_path,
    )

    assert attestation["attestation_status"] == "GENERALIZED_CLOSURE_CONFIRMED"
    assert attestation["blocking_issues"] == []
    assert attestation["closure_conditions"]["scope_generalized_confirmed"]["status"] == "SATISFIED"
    assert attestation["closure_conditions"]["validator_visible_non_probe_chain"]["status"] == "SATISFIED"
    assert attestation["closure_conditions"]["validator_visible_non_probe_chain"]["evidence"]["validatedArtifacts_count"] == 1
    assert attestation["closure_conditions"]["validator_visible_non_probe_chain"]["evidence"]["ledgerIds_count"] == 1
    assert attestation["closure_conditions"]["validator_visible_non_probe_chain"]["evidence"]["pointers_count"] == 1
    assert attestation["confirming_run_ids"] == ["run.generalized_coverage.guard.v1"]
