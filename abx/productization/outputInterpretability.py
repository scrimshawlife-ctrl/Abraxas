from __future__ import annotations

from abx.productization.types import OutputInterpretabilityRecord


def build_output_interpretability_records() -> list[OutputInterpretabilityRecord]:
    return [
        OutputInterpretabilityRecord("interp.audit.api", "product.api.governance_audits", "partner_integration", "interpretable", "explicit"),
        OutputInterpretabilityRecord("interp.scorecard.cli", "product.cli.scorecard_bundle", "support_steward", "interpretable", "explicit"),
        OutputInterpretabilityRecord("interp.demo.training", "product.demo.training_mode", "training_participant", "bounded_interpretable", "explicit"),
        OutputInterpretabilityRecord("interp.legacy.csv", "product.legacy.csv_export", "academic_research", "caution_required", "partial"),
    ]
