from __future__ import annotations

from abx.boundary.interfaceContracts import build_interface_contracts


def classify_interface_surfaces() -> dict[str, list[str]]:
    by_exposure: dict[str, list[str]] = {}
    for contract in build_interface_contracts():
        by_exposure.setdefault(contract.exposure, []).append(contract.interface_id)
    for key in by_exposure:
        by_exposure[key] = sorted(by_exposure[key])
    return by_exposure


def detect_redundant_entrypoints() -> list[str]:
    seen_signature: dict[tuple[tuple[str, ...], tuple[str, ...]], str] = {}
    duplicates: list[str] = []
    for contract in build_interface_contracts():
        key = (tuple(contract.required_fields), tuple(contract.optional_fields))
        if key in seen_signature:
            duplicates.append(f"{seen_signature[key]}::{contract.interface_id}")
        else:
            seen_signature[key] = contract.interface_id
    return sorted(duplicates)
