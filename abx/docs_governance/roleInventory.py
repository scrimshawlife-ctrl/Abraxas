from __future__ import annotations

from abx.docs_governance.types import OnboardingEntryRecord, RoleEntrypointRecord, RoleLegibilityRecord


def build_role_inventory() -> list[RoleLegibilityRecord]:
    return [
        RoleLegibilityRecord("role.operator", "operator", "operator.console.overview", "fully_legible", "operations"),
        RoleLegibilityRecord("role.maintainer", "maintainer", "docs/acceptance/README.md", "partial", "governance"),
        RoleLegibilityRecord("role.reviewer", "reviewer", "docs/branch_consolidation.md", "partial", "governance"),
        RoleLegibilityRecord("role.incident", "incident_responder", "abx/operations/incidents.py", "fully_legible", "operations"),
        RoleLegibilityRecord("role.legacy_owner", "future_owner", "docs/MERGE_CONFLICT_ANALYSIS.md", "legacy", "integration"),
    ]


def build_onboarding_entries() -> list[OnboardingEntryRecord]:
    return [
        OnboardingEntryRecord("onboard.operator", "operator", ["operator.console.overview", "abx/operations/runbooks.py"], "overview_to_drilldown"),
        OnboardingEntryRecord("onboard.maintainer", "maintainer", ["docs/acceptance/README.md", "scripts/run_*_scorecard.py"], "overview_to_governance"),
    ]


def build_role_entrypoints() -> list[RoleEntrypointRecord]:
    return [
        RoleEntrypointRecord("entry.operator", "operator", "operator.console.overview", ["operator.console.scorecards", "operator.console.trace_drilldown"]),
        RoleEntrypointRecord("entry.maintainer", "maintainer", "docs/acceptance/README.md", ["abx/governance/health_scorecard.py", "scripts/run_doc_scorecard.py"]),
        RoleEntrypointRecord("entry.incident", "incident_responder", "abx/operations/incidents.py", ["abx/operations/runbooks.py", "scripts/run_handoff_audit.py"]),
    ]
