"""Deterministic manifest generator for ABX-Runes."""

from __future__ import annotations

import json
from pathlib import Path

from abraxas.runes.registry import load_registry


def build_manifest(registry_path: str | Path | None = None) -> dict:
    if registry_path is None:
        registry_path = Path(__file__).resolve().parents[0] / "registry.json"
    registry_path = Path(registry_path)
    registry_payload = json.loads(registry_path.read_text())
    bindings = load_registry(registry_path)

    return {
        "version": registry_payload.get("version"),
        "generated": registry_payload.get("generated"),
        "registry_type": registry_payload.get("registry_type"),
        "runes": [
            {
                "rune_id": binding.rune_id,
                "short_name": binding.short_name,
                "name": binding.name,
                "capability": binding.capability,
                "version": binding.version,
                "inputs": binding.inputs,
                "outputs": binding.outputs,
                "definition_path": binding.definition_path,
                "sigil_path": binding.sigil_path,
                "operator_path": binding.operator_path,
            }
            for binding in bindings
        ],
    }


def write_manifest(path: str | Path | None = None) -> Path:
    if path is None:
        path = Path(__file__).resolve().parents[0] / "manifest.json"
    path = Path(path)
    manifest = build_manifest()
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return path
