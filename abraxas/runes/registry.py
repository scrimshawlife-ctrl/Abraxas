"""Canonical ABX-Runes registry and discovery helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from abraxas.runes.models import RuneDefinition


@dataclass(frozen=True)
class RuneBinding:
    rune_id: str
    short_name: str
    name: str
    version: str
    capability: str
    inputs: list[str]
    outputs: list[str]
    definition_path: str
    sigil_path: str
    operator_path: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_registry(registry_path: str | Path | None = None) -> list[RuneBinding]:
    if registry_path is None:
        registry_path = _repo_root() / "abraxas" / "runes" / "registry.json"
    registry_path = Path(registry_path)
    payload = json.loads(registry_path.read_text())
    bindings: list[RuneBinding] = []

    # Load traditional runes
    for entry in payload.get("runes", []):
        definition_path = _repo_root() / entry["definition_path"]
        definition = RuneDefinition(**json.loads(definition_path.read_text()))
        capability = f"rune:{definition.short_name.lower()}"
        operator_module = definition.short_name.lower()
        operator_path = f"abraxas.runes.operators.{operator_module}:apply_{operator_module}"
        bindings.append(
            RuneBinding(
                rune_id=definition.id,
                short_name=definition.short_name,
                name=definition.name,
                version=definition.introduced_version,
                capability=capability,
                inputs=definition.inputs,
                outputs=definition.outputs,
                definition_path=str(entry["definition_path"]),
                sigil_path=str(entry["sigil_path"]),
                operator_path=operator_path,
            )
        )

    # Load capability contracts (v2.0+ - for ABX-Runes coupling)
    for cap_entry in payload.get("capabilities", []):
        bindings.append(
            RuneBinding(
                rune_id=cap_entry["rune_id"],
                short_name=cap_entry["capability_id"].split(".")[-1],
                name=cap_entry["capability_id"],
                version=cap_entry["version"],
                capability=cap_entry["capability_id"],
                inputs=[],
                outputs=[],
                definition_path="",
                sigil_path="",
                operator_path=cap_entry["operator_path"],
            )
        )

    return bindings


def list_capabilities(bindings: Iterable[RuneBinding] | None = None) -> list[str]:
    bindings = list(bindings or load_registry())
    return sorted({binding.capability for binding in bindings})


def list_runes_by_capability(
    capability: str, bindings: Iterable[RuneBinding] | None = None
) -> list[RuneBinding]:
    bindings = list(bindings or load_registry())
    return [binding for binding in bindings if binding.capability == capability]


def describe_rune(rune_id: str, bindings: Iterable[RuneBinding] | None = None) -> RuneBinding:
    bindings = list(bindings or load_registry())
    for binding in bindings:
        if binding.rune_id == rune_id:
            return binding
    raise KeyError(f"Unknown rune id: {rune_id}")


def wiring_sanity_check(required_capabilities: list[str] | None = None) -> dict[str, list[str]]:
    bindings = load_registry()
    seen: set[str] = set()
    duplicates: list[str] = []
    for binding in bindings:
        if binding.rune_id in seen:
            duplicates.append(binding.rune_id)
        seen.add(binding.rune_id)

    missing: list[str] = []
    if required_capabilities:
        available = {binding.capability for binding in bindings}
        missing = [cap for cap in required_capabilities if cap not in available]

    return {
        "duplicate_rune_ids": duplicates,
        "missing_capabilities": missing,
    }
