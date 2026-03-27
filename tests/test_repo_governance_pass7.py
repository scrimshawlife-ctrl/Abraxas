from __future__ import annotations

from pathlib import Path

from abx.governance.pruning_audit import pruning_audit_report
from abx.governance.repo_audit import build_baseline_seal, build_release_readiness, build_repo_audit
from abx.governance.schema_inventory import schema_inventory_report
from abx.governance.source_of_truth import build_source_of_truth_report, check_derived_surface_misuse


def test_schema_inventory_is_deterministic() -> None:
    a = schema_inventory_report()
    b = schema_inventory_report()
    assert a == b
    assert a["classificationCounts"]["CANONICAL"] >= 1


def test_source_of_truth_and_derived_misuse_detection() -> None:
    report = build_source_of_truth_report()
    assert len(report["domains"]) >= 6

    misuse = check_derived_surface_misuse(
        domain="runtime_frame",
        asserted_authority="abx.resonance_frame.FrameProjection.v1",
    )
    assert misuse["status"] == "BROKEN"
    assert "derived-surface-used-as-authority" in misuse["issues"]


def test_pruning_audit_is_stable() -> None:
    root = Path(__file__).resolve().parent.parent
    a = pruning_audit_report(root)
    b = pruning_audit_report(root)
    assert a == b
    assert "deadPaths" in a
    assert "legacySurfaces" in a


def test_repo_audit_and_readiness_artifacts() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    audit_a = build_repo_audit(repo_root=repo_root)
    audit_b = build_repo_audit(repo_root=repo_root)
    assert audit_a.__dict__ == audit_b.__dict__
    assert "coupling_audit" in audit_a.enforced_checks
    assert "dead_path_candidates" in audit_a.reported_only_checks

    readiness = build_release_readiness(repo_root=repo_root)
    assert readiness.artifact_type == "ReleaseCandidateReadinessArtifact.v1"
    assert isinstance(readiness.blockers, list)

    seal = build_baseline_seal(repo_root=repo_root)
    assert seal["status"] in {"SEALED", "UNSEALED"}
    assert "seal_hash" in seal
