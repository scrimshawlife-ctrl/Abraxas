from __future__ import annotations

from abx.productization.packagingContracts import build_packaging_contracts


def classify_package_types() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {
        "canonical_package": [],
        "adapted_package": [],
        "tiered_package": [],
        "bounded_package": [],
        "legacy_package": [],
        "not_computable": [],
    }
    for row in build_packaging_contracts():
        key = row.package_class if row.package_class in out else "not_computable"
        out[key].append(row.contract_id)
    return {k: sorted(v) for k, v in out.items()}
