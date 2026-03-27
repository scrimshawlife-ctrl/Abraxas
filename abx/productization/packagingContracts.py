from __future__ import annotations

from abx.productization.types import PackagingContractRecord


def build_packaging_contracts() -> list[PackagingContractRecord]:
    return [
        PackagingContractRecord("contract.api.audit.v1", "audit_api", "canonical_package", "compatible", "bounded", ["audit_exports"]),
        PackagingContractRecord("contract.cli.scorecard.v1", "scorecard_cli", "tiered_package", "compatible", "bounded", ["scorecard_exports"]),
        PackagingContractRecord("contract.demo.training.v1", "training_demo", "adapted_package", "partial", "bounded", ["training_demo"]),
        PackagingContractRecord("contract.legacy.csv.v0", "legacy_csv", "legacy_package", "partial", "loosely_bounded", ["legacy_exports"]),
    ]
