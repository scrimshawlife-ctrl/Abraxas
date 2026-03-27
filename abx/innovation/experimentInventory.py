from __future__ import annotations

from abx.innovation.types import ExperimentSurfaceRecord


def build_experiment_surface_inventory() -> list[ExperimentSurfaceRecord]:
    return [
        ExperimentSurfaceRecord(
            experiment_id="exp-hypothesis-routing-v2",
            capability="decision-routing",
            surface_kind="prototype",
            runtime_scope="sandbox",
            influence_boundary="evaluation_only",
            owner="decision-governance",
            governance_layers=["policy", "epistemics", "security"],
        ),
        ExperimentSurfaceRecord(
            experiment_id="exp-latency-compression-3",
            capability="runtime-performance",
            surface_kind="canary-eligible",
            runtime_scope="shared-staging",
            influence_boundary="bounded_canary",
            owner="performance-governance",
            governance_layers=["performance", "deployment", "security"],
        ),
        ExperimentSurfaceRecord(
            experiment_id="exp-symbolic-memory-bridge",
            capability="knowledge-continuity",
            surface_kind="sandbox-only",
            runtime_scope="isolated-lab",
            influence_boundary="production-prohibited",
            owner="knowledge-governance",
            governance_layers=["knowledge", "boundary"],
        ),
        ExperimentSurfaceRecord(
            experiment_id="exp-legacy-shadow-parser",
            capability="ingest-normalization",
            surface_kind="legacy-experiment",
            runtime_scope="unknown",
            influence_boundary="unbounded-risk",
            owner="unassigned",
            governance_layers=["boundary"],
        ),
    ]
