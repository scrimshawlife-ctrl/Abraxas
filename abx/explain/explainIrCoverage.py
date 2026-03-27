from __future__ import annotations

from abx.explain.explainOwnership import explain_ownership
from abx.observability.types import ExplanationCoverageRecord


def build_explain_coverage() -> list[ExplanationCoverageRecord]:
    owners = explain_ownership()
    rows = [
        ExplanationCoverageRecord(surface_id="surface.runtime.workflow", coverage_status="COVERED", owner=owners["surface.runtime.workflow"]),
        ExplanationCoverageRecord(surface_id="surface.boundary.validation", coverage_status="COVERED", owner=owners["surface.boundary.validation"]),
        ExplanationCoverageRecord(surface_id="surface.operator.console", coverage_status="PARTIAL", owner=owners["surface.operator.console"]),
    ]
    return sorted(rows, key=lambda x: x.surface_id)
