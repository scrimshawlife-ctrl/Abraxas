from __future__ import annotations

from abx.productization.types import ProductSurfaceRecord


def build_product_surface_inventory() -> list[ProductSurfaceRecord]:
    return [
        ProductSurfaceRecord("product.api.governance_audits", "audit_exports", "partner_integration", "canonical_external", "contract.api.audit.v1", "platform"),
        ProductSurfaceRecord("product.cli.scorecard_bundle", "scorecard_exports", "support_steward", "semi_external_package", "contract.cli.scorecard.v1", "governance"),
        ProductSurfaceRecord("product.demo.training_mode", "training_demo", "training_participant", "experimental", "contract.demo.training.v1", "operations"),
        ProductSurfaceRecord("product.legacy.csv_export", "legacy_exports", "academic_research", "legacy", "contract.legacy.csv.v0", "integration"),
        ProductSurfaceRecord("product.internal.operator_console", "operator_console", "internal_operator", "internal_only", "internal", "operations"),
    ]
