from __future__ import annotations

from datetime import date
from pathlib import Path

from abx.governance.breaking_change_detection import scan_breaking_changes
from abx.governance.canonical_manifest import BASELINE_ID, BASELINE_VERSION, build_canonical_manifest
from abx.governance.health_scorecard import build_repo_health_scorecard
from abx.governance.migration_guards import run_migration_guards
from abx.governance.repo_audit import build_repo_audit
from abx.governance.types import BaselineReleasePrepArtifact
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_baseline_release_prep(*, repo_root: Path) -> BaselineReleasePrepArtifact:
    manifest = build_canonical_manifest()
    audit = build_repo_audit(repo_root=repo_root)
    guards = run_migration_guards()
    breaking = scan_breaking_changes()
    health = build_repo_health_scorecard(repo_root=repo_root)

    blockers = sorted(
        set(audit.blockers)
        | set(health.blockers)
        | ({"migration-breaking"} if guards.status == "BREAKING" else set())
        | ({"migration-required"} if guards.status == "MIGRATION_REQUIRED" else set())
        | ({"breaking-change-report"} if breaking.status == "BREAKING" else set())
    )

    if not manifest.members:
        release_state = "NOT_COMPUTABLE"
    elif blockers:
        release_state = "BLOCKED"
    elif health.overall_status == "WARN":
        release_state = "NEARLY_READY"
    else:
        release_state = "READY_TO_TAG"

    evidence_refs = [
        manifest.artifact_type,
        audit.artifact_type,
        guards.artifact_type,
        breaking.artifact_type,
        health.artifact_type,
    ]

    release_notes_scaffold = {
        "summary": "First governed baseline freeze candidate.",
        "highlights": [
            "Canonical manifest frozen and diffable.",
            "Migration guards and breaking scan enabled.",
            "Deterministic health scorecard included.",
        ],
        "blockers": blockers,
    }

    tag_metadata = {
        "tag_name": f"baseline/{BASELINE_ID.lower()}",
        "baseline_id": BASELINE_ID,
        "baseline_version": BASELINE_VERSION,
        "prepared_on": str(date.today()),
    }

    payload = {
        "baseline_id": BASELINE_ID,
        "release_state": release_state,
        "blockers": blockers,
        "evidence_refs": evidence_refs,
        "tag_metadata": tag_metadata,
    }
    prep_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))

    return BaselineReleasePrepArtifact(
        artifact_type="BaselineReleasePrepArtifact.v1",
        artifact_id="baseline-release-prep-abx",
        baseline_id=BASELINE_ID,
        release_state=release_state,
        blockers=blockers,
        evidence_refs=evidence_refs,
        release_notes_scaffold=release_notes_scaffold,
        tag_metadata=tag_metadata,
        prep_hash=prep_hash,
    )
