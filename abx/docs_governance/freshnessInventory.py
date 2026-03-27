from __future__ import annotations

from abx.docs_governance.types import DocumentationFreshnessRecord


def build_freshness_inventory() -> list[DocumentationFreshnessRecord]:
    return [
        DocumentationFreshnessRecord("fresh.doc.operating_manual", "doc.operating_manual", "fresh", "manually_maintained_with_dependency", "operations"),
        DocumentationFreshnessRecord("fresh.doc.scorecards", "doc.scorecard_scripts", "fresh", "generated_on_refresh", "governance"),
        DocumentationFreshnessRecord("fresh.doc.acceptance", "doc.acceptance_spec", "monitored", "manually_maintained_with_dependency", "governance"),
        DocumentationFreshnessRecord("fresh.doc.legacy_merge", "doc.legacy_merge_analysis", "stale_candidate", "archival", "integration"),
    ]
