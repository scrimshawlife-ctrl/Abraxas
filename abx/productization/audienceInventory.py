from __future__ import annotations

from abx.productization.types import AudienceEntrypointRecord, AudienceLegibilityRecord


def build_audience_inventory() -> list[AudienceLegibilityRecord]:
    return [
        AudienceLegibilityRecord("aud.customer", "customer_user", "product.api.governance_audits", "fully_legible", "contract.api.audit.v1"),
        AudienceLegibilityRecord("aud.partner", "partner_integration", "product.api.governance_audits", "fully_legible", "contract.api.audit.v1"),
        AudienceLegibilityRecord("aud.support", "support_steward", "product.cli.scorecard_bundle", "partial", "contract.cli.scorecard.v1"),
        AudienceLegibilityRecord("aud.research", "academic_research", "product.legacy.csv_export", "legacy", "contract.legacy.csv.v0"),
    ]


def build_audience_entrypoints() -> list[AudienceEntrypointRecord]:
    return [
        AudienceEntrypointRecord("entry.customer", "customer_user", "product.api.governance_audits", ["scripts/run_product_scorecard.py"]),
        AudienceEntrypointRecord("entry.partner", "partner_integration", "product.api.governance_audits", ["scripts/run_packaging_audit.py"]),
        AudienceEntrypointRecord("entry.support", "support_steward", "product.cli.scorecard_bundle", ["scripts/run_output_boundedness_audit.py"]),
    ]
