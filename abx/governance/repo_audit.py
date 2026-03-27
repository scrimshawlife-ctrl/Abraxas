from __future__ import annotations

from datetime import date
from pathlib import Path

from abx.coupling_audit import audit_coupling
from abx.governance.pruning_audit import pruning_audit_report
from abx.governance.schema_inventory import schema_inventory_report
from abx.governance.source_of_truth import build_source_of_truth_report
from abx.governance.types import RepoAuditArtifact, ReleaseCandidateReadinessArtifact
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_repo_audit(*, repo_root: Path) -> RepoAuditArtifact:
    schema = schema_inventory_report()
    source = build_source_of_truth_report()
    pruning = pruning_audit_report(repo_root)
    coupling = audit_coupling(repo_root=repo_root)

    schema_counts = dict(schema.get("classificationCounts") or {})
    blocker_flags: list[str] = []
    if schema_counts.get("LEGACY", 0) > 0:
        blocker_flags.append("legacy-schema-surfaces-present")
    if schema_counts.get("DEPRECATED_CANDIDATE", 0) > 0:
        blocker_flags.append("deprecation-candidates-not-resolved")
    if coupling.status == "BROKEN":
        blocker_flags.append("coupling-audit-broken")
    if pruning.get("deadPaths"):
        blocker_flags.append("dead-paths-require-pruning-plan")

    payload = {
        "schema": schema,
        "source": source,
        "pruning": pruning,
        "coupling_status": coupling.status,
        "blockers": sorted(set(blocker_flags)),
    }
    audit_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))

    return RepoAuditArtifact(
        artifact_type="RepoAuditArtifact.v1",
        artifact_id="repo-audit-abx",
        generated_at=str(date.today()),
        schema_summary={k: int(v) for k, v in sorted(schema_counts.items())},
        source_of_truth_summary={"domains": len(source.get("domains") or [])},
        pruning_summary={
            "legacy_surface_count": len(pruning.get("legacySurfaces") or []),
            "dead_path_count": len(pruning.get("deadPaths") or []),
        },
        coupling_summary={
            "status": coupling.status,
            "suspect_count": len(coupling.suspect_couplings),
            "prohibited_count": len(coupling.prohibited_couplings),
        },
        blockers=sorted(set(blocker_flags)),
        enforced_checks=["coupling_audit", "schema_classification", "source_of_truth_mapping"],
        reported_only_checks=["dead_path_candidates", "staged_deprecations"],
        audit_hash=audit_hash,
    )


def build_release_readiness(*, repo_root: Path) -> ReleaseCandidateReadinessArtifact:
    audit = build_repo_audit(repo_root=repo_root)
    status = "READY" if not audit.blockers else "BLOCKED"

    canonical_manifest = {
        "runtime_frame": "ResonanceFrame.v1",
        "proof_chain": "ProofChainArtifact.v1",
        "closure_summary": "ClosureSummaryArtifact.v1",
        "promotion_pack": "PromotionPackArtifact.v1",
        "continuity": "ContinuitySummaryArtifact.v1",
    }

    staged_deprecations = [
        "scripts/run_frame_assembly.py",
        "scripts/run_adapter_audit.py",
        "abx/operator_console.py::inspect-validation",
    ]
    recommendations = [
        "Migrate operator consumers to SourceOfTruthReport.v1 and RepoAuditArtifact.v1 outputs.",
        "Remove high-confidence dead scripts after one release cycle with compatibility warning.",
        "Keep derived-surface misuse checks in CI as non-optional gate.",
    ]

    readiness_payload = {
        "audit_hash": audit.audit_hash,
        "status": status,
        "blockers": audit.blockers,
        "canonical_manifest": canonical_manifest,
        "staged_deprecations": staged_deprecations,
    }
    readiness_hash = sha256_bytes(dumps_stable(readiness_payload).encode("utf-8"))

    return ReleaseCandidateReadinessArtifact(
        artifact_type="ReleaseCandidateReadinessArtifact.v1",
        artifact_id="release-readiness-abx",
        status=status,
        blockers=list(audit.blockers),
        canonical_manifest=canonical_manifest,
        staged_deprecations=staged_deprecations,
        recommendations=recommendations,
        readiness_hash=readiness_hash,
    )


def build_baseline_seal(*, repo_root: Path) -> dict[str, object]:
    audit = build_repo_audit(repo_root=repo_root)
    readiness = build_release_readiness(repo_root=repo_root)
    payload = {
        "audit": audit.__dict__,
        "readiness": readiness.__dict__,
        "status": "SEALED" if readiness.status == "READY" else "UNSEALED",
    }
    payload["seal_hash"] = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return payload
