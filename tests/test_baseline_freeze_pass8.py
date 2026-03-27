from __future__ import annotations

from pathlib import Path

from abx.governance.baseline_release_prep import build_baseline_release_prep
from abx.governance.breaking_change_detection import scan_breaking_changes
from abx.governance.canonical_manifest import build_canonical_manifest, manifest_diff_against_frozen
from abx.governance.health_scorecard import build_repo_health_scorecard
from abx.governance.migration_guards import run_migration_guards


def test_canonical_manifest_and_diff_are_deterministic() -> None:
    a = build_canonical_manifest()
    b = build_canonical_manifest()
    assert a.__dict__ == b.__dict__

    diff_a = manifest_diff_against_frozen()
    diff_b = manifest_diff_against_frozen()
    assert diff_a == diff_b
    assert diff_a["status"] in {"VALID", "DRIFT", "NOT_COMPUTABLE"}


def test_migration_guard_report_stability() -> None:
    a = run_migration_guards()
    b = run_migration_guards()
    assert a.__dict__ == b.__dict__
    assert a.status in {
        "COMPATIBLE_ADDITIVE",
        "COMPATIBLE_INTERNAL",
        "MIGRATION_REQUIRED",
        "BREAKING",
        "NOT_COMPUTABLE",
    }


def test_breaking_change_scan_classification_is_stable() -> None:
    report = scan_breaking_changes()
    assert report.status in {"NON_BREAKING", "MIGRATION_REQUIRED", "BREAKING", "NOT_COMPUTABLE"}

    second = scan_breaking_changes()
    assert report.__dict__ == second.__dict__


def test_health_scorecard_and_release_prep_are_deterministic() -> None:
    repo_root = Path(__file__).resolve().parent.parent

    health_a = build_repo_health_scorecard(repo_root=repo_root)
    health_b = build_repo_health_scorecard(repo_root=repo_root)
    assert health_a.__dict__ == health_b.__dict__
    assert isinstance(health_a.component_scores, dict)
    assert len(health_a.component_scores) >= 5

    prep_a = build_baseline_release_prep(repo_root=repo_root)
    prep_b = build_baseline_release_prep(repo_root=repo_root)
    assert prep_a.__dict__ == prep_b.__dict__
    assert prep_a.release_state in {"READY_TO_TAG", "NEARLY_READY", "BLOCKED", "NOT_COMPUTABLE"}
