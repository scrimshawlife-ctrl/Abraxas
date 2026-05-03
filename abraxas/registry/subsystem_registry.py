from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import hashlib

import yaml


@dataclass(frozen=True)
class RegistryLoadResult:
    registry_path: str
    schema_version: str
    registry_id: str
    subsystem_count: int
    subsystem_ids: tuple[str, ...]
    canonical_hash: str
    raw: dict[str, Any]


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_subsystem_registry(path: str | Path = ".aal/subsystem_registry.v1.yaml") -> RegistryLoadResult:
    registry_path = Path(path)
    if not registry_path.exists():
        raise FileNotFoundError(f"Subsystem registry not found: {registry_path}")

    with registry_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if not isinstance(raw, dict):
        raise ValueError("Subsystem registry must decode to an object")

    schema_version = raw.get("schema_version")
    registry_id = raw.get("registry_id")
    subsystems = raw.get("subsystems")

    if schema_version != "SubsystemRegistry.v1":
        raise ValueError(f"Unsupported registry schema_version: {schema_version}")
    if not isinstance(registry_id, str) or not registry_id:
        raise ValueError("registry_id must be a non-empty string")
    if not isinstance(subsystems, list):
        raise ValueError("subsystems must be a list")

    subsystem_ids: list[str] = []
    for row in subsystems:
        if not isinstance(row, dict):
            raise ValueError("Each subsystem row must be an object")
        subsystem_id = row.get("subsystem_id")
        if not isinstance(subsystem_id, str) or not subsystem_id:
            raise ValueError("Each subsystem row requires subsystem_id")
        subsystem_ids.append(subsystem_id)

    if len(subsystem_ids) != len(set(subsystem_ids)):
        raise ValueError("Duplicate subsystem_id values found")

    sorted_ids = tuple(sorted(subsystem_ids))
    canonical_hash = _sha256_text(_canonical_json(raw))
    return RegistryLoadResult(
        registry_path=str(registry_path),
        schema_version=schema_version,
        registry_id=registry_id,
        subsystem_count=len(subsystem_ids),
        subsystem_ids=sorted_ids,
        canonical_hash=canonical_hash,
        raw=raw,
    )
