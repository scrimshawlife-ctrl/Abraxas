from __future__ import annotations

from abx.closure.types import ClosureSurfaceRecord


WAIVER_BY_DOMAIN: dict[str, list[str]] = {
    "domain.docs": ["stale_doc_burden"],
    "domain.meta": ["supersession_conflict_visibility"],
}


def build_closure_surface_inventory() -> list[ClosureSurfaceRecord]:
    rows = [
        ClosureSurfaceRecord("surface.baseline", "domain.baseline", "RepoHealthScorecard.v1", [], []),
        ClosureSurfaceRecord("surface.security", "domain.security", "SecurityIntegrityScorecard.v1", ["domain.baseline"], []),
        ClosureSurfaceRecord("surface.deployment", "domain.deployment", "DeploymentGovernanceScorecard.v1", ["domain.baseline"], []),
        ClosureSurfaceRecord("surface.epistemic", "domain.epistemic", "EpistemicQualityScorecard.v1", ["domain.baseline"], []),
        ClosureSurfaceRecord("surface.docs", "domain.docs", "DocumentationLegibilityScorecard.v1", ["domain.baseline"], WAIVER_BY_DOMAIN["domain.docs"]),
        ClosureSurfaceRecord("surface.product", "domain.product", "ProductizationGovernanceScorecard.v1", ["domain.docs", "domain.deployment"], []),
        ClosureSurfaceRecord("surface.performance", "domain.performance", "PerformanceResourceScorecard.v1", ["domain.deployment"], []),
        ClosureSurfaceRecord("surface.innovation", "domain.innovation", "ExperimentationGovernanceScorecard.v1", ["domain.meta"], []),
        ClosureSurfaceRecord("surface.meta", "domain.meta", "MetaGovernanceScorecard.v1", ["domain.baseline"], WAIVER_BY_DOMAIN["domain.meta"]),
    ]
    return sorted(rows, key=lambda x: x.surface_id)
