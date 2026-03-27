from __future__ import annotations

from abx.epistemics.types import ValidationSurfaceRecord


def build_validation_surface_inventory() -> list[ValidationSurfaceRecord]:
    return [
        ValidationSurfaceRecord(
            validation_id="val.runtime.boundary_input",
            workflow="ingest",
            capability="input_envelope_validation",
            validation_kind="runtime_validation",
            trust_level="authoritative",
            owner="boundary",
        ),
        ValidationSurfaceRecord(
            validation_id="val.replay.invariance_gate",
            workflow="replay",
            capability="invariance_verification",
            validation_kind="replay_validation",
            trust_level="governed_derived",
            owner="governance",
        ),
        ValidationSurfaceRecord(
            validation_id="val.observability.trace_consistency",
            workflow="observability",
            capability="trace_consistency_check",
            validation_kind="comparison_validation",
            trust_level="monitored",
            owner="observability",
        ),
        ValidationSurfaceRecord(
            validation_id="val.forecast.outcome_coupling",
            workflow="forecast_review",
            capability="outcome_comparison",
            validation_kind="comparison_validation",
            trust_level="heuristic",
            owner="forecast",
        ),
        ValidationSurfaceRecord(
            validation_id="val.legacy.import_assertions",
            workflow="import_export",
            capability="legacy_assertions",
            validation_kind="policy_integrity_validation",
            trust_level="legacy_redundant_candidate",
            owner="integration",
        ),
    ]
