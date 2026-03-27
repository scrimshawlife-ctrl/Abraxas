from __future__ import annotations

from abx.rune_governance import check_rune_governance, check_validation_artifact_traceability


def test_rune_governance_report_materializes() -> None:
    report = check_rune_governance()
    assert isinstance(report.duplicate_rune_ids, list)
    assert isinstance(report.missing_contracts, list)
    assert isinstance(report.dependency_mismatch, list)
    assert isinstance(report.schema_drift, list)
    assert isinstance(report.forbidden_influence_leakage, list)


def test_validation_artifact_traceability_fails_closed_on_missing_fields() -> None:
    issues = check_validation_artifact_traceability({"runId": "RUN-1"})
    assert "missing-artifactId" in issues
    assert "missing-ledgerIds" in issues
    assert "missing-validatedArtifacts" in issues


def test_validation_artifact_traceability_passes_when_linked() -> None:
    issues = check_validation_artifact_traceability(
        {
            "runId": "RUN-1",
            "artifactId": "execution-validation-RUN-1",
            "validatedArtifacts": ["artifact-1"],
            "correlation": {"ledgerIds": ["record-1"]},
        }
    )
    assert issues == []
