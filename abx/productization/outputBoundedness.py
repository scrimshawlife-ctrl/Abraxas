from __future__ import annotations

from abx.productization.types import ProductBoundednessRecord


def build_output_boundedness_records() -> list[ProductBoundednessRecord]:
    return [
        ProductBoundednessRecord("bound.audit.api", "product.api.governance_audits", "partner_integration", "safe_complete_for_audience", "contract.api.audit.v1#caveats"),
        ProductBoundednessRecord("bound.scorecard.cli", "product.cli.scorecard_bundle", "support_steward", "bounded_limited", "contract.cli.scorecard.v1#limits"),
        ProductBoundednessRecord("bound.demo.training", "product.demo.training_mode", "training_participant", "degraded_but_usable", "contract.demo.training.v1#demo_limits"),
        ProductBoundednessRecord("bound.legacy.csv", "product.legacy.csv_export", "academic_research", "caution_required", "contract.legacy.csv.v0#caveats"),
    ]
