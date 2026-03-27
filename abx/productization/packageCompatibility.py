from __future__ import annotations

from abx.productization.packagingContracts import build_packaging_contracts


def classify_package_compatibility() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"compatible": [], "partial": [], "incompatible": [], "unknown": []}
    for row in build_packaging_contracts():
        key = row.compatibility if row.compatibility in out else "unknown"
        out[key].append(row.contract_id)
    return {k: sorted(v) for k, v in out.items()}


def detect_redundant_package_dialects() -> list[str]:
    seen: set[tuple[str, str]] = set()
    drift: list[str] = []
    for row in build_packaging_contracts():
        key = (row.package_name, row.package_class)
        if key in seen:
            drift.append(row.contract_id)
            continue
        seen.add(key)
    return sorted(drift)
