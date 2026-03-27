from __future__ import annotations

from abx.docs_governance.types import DocumentationSurfaceRecord


def build_doc_inventory() -> list[DocumentationSurfaceRecord]:
    return [
        DocumentationSurfaceRecord("doc.operating_manual", "abx/operations/operating_manual.py", "authoritative_reference", "operations.service_expectations", "operations"),
        DocumentationSurfaceRecord("doc.runbooks", "abx/operations/runbooks.py", "operator_guide", "operations.incidents", "operations"),
        DocumentationSurfaceRecord("doc.scorecard_scripts", "scripts/run_*_scorecard.py", "generated_summary", "scorecard_audits", "governance"),
        DocumentationSurfaceRecord("doc.acceptance_spec", "docs/acceptance/ABRAXAS_ACCEPTANCE_SPEC_v1.md", "maintainer_guide", "governance.health_scorecard", "governance"),
        DocumentationSurfaceRecord("doc.quickstart_api", "QUICKSTART_API.md", "onboarding_surface", "server.app", "platform"),
        DocumentationSurfaceRecord("doc.legacy_merge_analysis", "docs/MERGE_CONFLICT_ANALYSIS.md", "legacy_redundant_candidate", "historical_note", "integration"),
    ]
