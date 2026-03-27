from __future__ import annotations

from abx.productization.types import PackageTierRecord


def build_package_tiers() -> list[PackageTierRecord]:
    return [
        PackageTierRecord("tier.audit.standard", "audit_api", "standard", "full_semantics", ["rate_limits"]),
        PackageTierRecord("tier.scorecard.support", "scorecard_cli", "support", "bounded_semantics", ["limited_drilldown"]),
        PackageTierRecord("tier.demo.training", "training_demo", "demo", "bounded_semantics", ["synthetic_data"]),
        PackageTierRecord("tier.legacy.csv", "legacy_csv", "legacy", "legacy_semantics", ["schema_drift_risk"]),
    ]
