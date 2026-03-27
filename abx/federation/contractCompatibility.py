from __future__ import annotations

from abx.federation.crossSystemContracts import build_cross_system_contracts


def classify_contract_compatibility() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for row in build_cross_system_contracts():
        grouped.setdefault(row.compatibility, []).append(row.contract_id)
    return {k: sorted(v) for k, v in sorted(grouped.items())}


def detect_duplicate_contract_shapes() -> list[str]:
    seen: dict[str, str] = {}
    dupes: list[str] = []
    for row in build_cross_system_contracts():
        key = row.contract_id.split(".v")[0]
        if key in seen:
            dupes.append(f"{seen[key]}::{row.contract_id}")
        else:
            seen[key] = row.contract_id
    return sorted(dupes)
