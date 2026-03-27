from __future__ import annotations

from abx.observability.types import ObservabilitySurfaceRecord


def build_surface_inventory() -> list[ObservabilitySurfaceRecord]:
    rows = [
        ObservabilitySurfaceRecord("surface.runtime.workflow", "runtime_orchestrator", "canonical", "ACTIVE", True),
        ObservabilitySurfaceRecord("surface.boundary.validation", "boundary", "canonical", "ACTIVE", True),
        ObservabilitySurfaceRecord("surface.boundary.scorecard", "boundary", "derived", "ACTIVE", False),
        ObservabilitySurfaceRecord("surface.resilience.scorecard", "resilience", "derived", "ACTIVE", False),
        ObservabilitySurfaceRecord("surface.scale.scorecard", "scale", "derived", "ACTIVE", False),
        ObservabilitySurfaceRecord("surface.operator.console", "operator_console", "legacy", "ACTIVE", True),
    ]
    return sorted(rows, key=lambda x: x.surface_id)
