from __future__ import annotations

from pathlib import Path

from abx.governance.breaking_change_detection import scan_breaking_changes
from abx.governance.canonical_manifest import BASELINE_ID, manifest_diff_against_frozen
from abx.governance.migration_guards import run_migration_guards
from abx.governance.repo_audit import build_repo_audit
from abx.governance.types import RepoHealthScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _score_bool(ok: bool) -> int:
    return 100 if ok else 40


def build_repo_health_scorecard(*, repo_root: Path) -> RepoHealthScorecard:
    audit = build_repo_audit(repo_root=repo_root)
    manifest_diff = manifest_diff_against_frozen()
    guards = run_migration_guards()
    breaks = scan_breaking_changes()

    component_scores = {
        "manifest_freeze": _score_bool(manifest_diff.get("status") == "VALID"),
        "migration_guards": _score_bool(guards.status in {"COMPATIBLE_INTERNAL", "COMPATIBLE_ADDITIVE"}),
        "breaking_change_detection": _score_bool(breaks.status in {"NON_BREAKING"}),
        "schema_governance": _score_bool(audit.schema_summary.get("LEGACY", 0) == 0),
        "pruning_burden": _score_bool(audit.pruning_summary.get("dead_path_count", 0) == 0),
        "coupling": _score_bool(audit.coupling_summary.get("status") != "BROKEN"),
    }

    blockers = sorted(
        set(audit.blockers)
        | ({"migration-guard-breaking"} if guards.status == "BREAKING" else set())
        | ({"migration-guard-required"} if guards.status == "MIGRATION_REQUIRED" else set())
        | ({"manifest-drift-detected"} if manifest_diff.get("status") == "DRIFT" else set())
        | ({"breaking-change-detected"} if breaks.status == "BREAKING" else set())
    )

    weak_zones = sorted(k for k, v in component_scores.items() if v < 100)

    average_score = sum(component_scores.values()) / max(len(component_scores), 1)
    if blockers:
        overall_status = "BLOCKED"
    elif average_score >= 90:
        overall_status = "HEALTHY"
    elif average_score >= 70:
        overall_status = "WARN"
    else:
        overall_status = "CRITICAL"

    payload = {
        "baseline_id": BASELINE_ID,
        "overall_status": overall_status,
        "component_scores": component_scores,
        "blockers": blockers,
        "weak_zones": weak_zones,
    }
    scorecard_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))

    return RepoHealthScorecard(
        artifact_type="RepoHealthScorecard.v1",
        artifact_id="repo-health-scorecard-abx",
        baseline_id=BASELINE_ID,
        overall_status=overall_status,
        component_scores=component_scores,
        blockers=blockers,
        weak_zones=weak_zones,
        scorecard_hash=scorecard_hash,
    )
