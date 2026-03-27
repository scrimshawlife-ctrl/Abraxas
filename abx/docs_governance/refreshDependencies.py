from __future__ import annotations

from abx.docs_governance.types import RefreshDependencyRecord


def build_refresh_dependencies() -> list[RefreshDependencyRecord]:
    return [
        RefreshDependencyRecord("dep.operating_manual.runbooks", "doc.operating_manual", "abx/operations/runbooks.py", "runtime_dependency"),
        RefreshDependencyRecord("dep.acceptance.scorecard", "doc.acceptance_spec", "scripts/run_*_scorecard.py", "generated_dependency"),
        RefreshDependencyRecord("dep.quickstart.server", "doc.quickstart_api", "abx/server/app.py", "runtime_dependency"),
        RefreshDependencyRecord("dep.legacy.merge", "doc.legacy_merge_analysis", "docs/branch_consolidation.md", "historical_dependency"),
    ]
