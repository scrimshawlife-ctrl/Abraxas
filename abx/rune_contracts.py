from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from abraxas.runes.models import RuneDefinition


class ABXRuneIO(BaseModel):
    name: str
    type: str
    required: bool = True


class ABXRuneOutput(BaseModel):
    name: str
    type: str


class ABXRuneContract(BaseModel):
    rune_id: str
    acronym: str
    version: str
    lane: Literal["ACTIVE", "SHADOW", "CANARY", "DEPRECATED"] = "ACTIVE"
    category: Literal[
        "INGEST",
        "DETECT",
        "VALIDATE",
        "ENFORCE",
        "ROUTE",
        "SCHEDULE",
        "ARTIFACT",
        "CONTINUITY",
        "EXPLAIN",
    ] = "DETECT"
    inputs: list[ABXRuneIO] = Field(default_factory=list)
    outputs: list[ABXRuneOutput] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    influence_policy: Literal["NONE", "BOUNDED", "DIRECT"] = "BOUNDED"
    determinism_rule: str = "identical_input_identical_output_no_randomness_no_time_variation"
    provenance_fields: list[str] = Field(default_factory=lambda: ["run_id", "artifact_id"])
    failure_modes: list[str] = Field(default_factory=list)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_registry_payload(registry_path: Path | None = None) -> dict:
    if registry_path is None:
        registry_path = _repo_root() / "abraxas" / "runes" / "registry.json"
    return json.loads(registry_path.read_text(encoding="utf-8"))


_LANES = {"ACTIVE", "SHADOW", "CANARY", "DEPRECATED"}
_INFLUENCE = {"NONE", "BOUNDED", "DIRECT"}
_CATEGORIES = {
    "INGEST",
    "DETECT",
    "VALIDATE",
    "ENFORCE",
    "ROUTE",
    "SCHEDULE",
    "ARTIFACT",
    "CONTINUITY",
    "EXPLAIN",
}


def _category_for_layer(layer: str) -> str:
    normalized = (layer or "").strip().lower()
    if normalized in {"ingest", "input", "acquire"}:
        return "INGEST"
    if normalized in {"governance", "validation"}:
        return "VALIDATE"
    if normalized in {"detect", "core"}:
        return "DETECT"
    return "ENFORCE"


def _metadata_lane(entry: dict, metadata: dict) -> str:
    lane = str(entry.get("lane") or metadata.get("lane") or "ACTIVE").upper()
    return lane if lane in _LANES else "ACTIVE"


def _metadata_influence(entry: dict, metadata: dict) -> str:
    policy = str(entry.get("influence_policy") or metadata.get("influence_policy") or "BOUNDED").upper()
    return policy if policy in _INFLUENCE else "BOUNDED"


def _metadata_category(metadata: dict, layer: str) -> str:
    raw = str(metadata.get("category") or "").upper()
    if raw in _CATEGORIES:
        return raw
    return _category_for_layer(layer)


def _typed_inputs(definition: RuneDefinition, metadata: dict) -> list[ABXRuneIO]:
    raw = metadata.get("inputs")
    if isinstance(raw, list) and raw:
        parsed: list[ABXRuneIO] = []
        for item in raw:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            parsed.append(
                ABXRuneIO(
                    name=str(item["name"]),
                    type=str(item.get("type") or "object"),
                    required=bool(item.get("required", True)),
                )
            )
        if parsed:
            return parsed
    return [ABXRuneIO(name=name, type="object", required=True) for name in definition.inputs]


def _typed_outputs(definition: RuneDefinition, metadata: dict) -> list[ABXRuneOutput]:
    raw = metadata.get("outputs")
    if isinstance(raw, list) and raw:
        parsed: list[ABXRuneOutput] = []
        for item in raw:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            parsed.append(ABXRuneOutput(name=str(item["name"]), type=str(item.get("type") or "object")))
        if parsed:
            return parsed
    return [ABXRuneOutput(name=name, type="object") for name in definition.outputs]


def _string_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw]


def load_abx_rune_contracts(registry_path: Path | None = None) -> list[ABXRuneContract]:
    payload = _load_registry_payload(registry_path)
    contracts: list[ABXRuneContract] = []

    for entry in payload.get("runes", []):
        definition_path = _repo_root() / entry["definition_path"]
        definition = RuneDefinition(**json.loads(definition_path.read_text(encoding="utf-8")))
        metadata = definition.metadata if isinstance(definition.metadata, dict) else {}
        dependencies = metadata.get("dependencies") if isinstance(metadata.get("dependencies"), list) else []
        provenance_fields = metadata.get("provenance_fields")
        failure_modes = metadata.get("failure_modes")
        determinism_rule = metadata.get("determinism_rule")

        contracts.append(
            ABXRuneContract(
                rune_id=definition.id,
                acronym=definition.short_name,
                version=definition.introduced_version,
                lane=_metadata_lane(entry, metadata),
                category=_metadata_category(metadata, definition.layer),
                inputs=_typed_inputs(definition, metadata),
                outputs=_typed_outputs(definition, metadata),
                dependencies=[str(dep) for dep in dependencies],
                influence_policy=_metadata_influence(entry, metadata),
                determinism_rule=(
                    str(determinism_rule)
                    if isinstance(determinism_rule, str) and determinism_rule
                    else "identical_input_identical_output_no_randomness_no_time_variation"
                ),
                provenance_fields=(
                    _string_list(provenance_fields)
                    if provenance_fields
                    else ["run_id", "rune_id", "artifact_id"]
                ),
                failure_modes=(
                    _string_list(failure_modes)
                    if failure_modes
                    else ["stub_blocked", "execution_failed", "schema_validation_failed"]
                ),
            )
        )

    return sorted(contracts, key=lambda c: c.rune_id)


def get_abx_rune_contract(rune_id: str, registry_path: Path | None = None) -> ABXRuneContract:
    for contract in load_abx_rune_contracts(registry_path):
        if contract.rune_id == rune_id:
            return contract
    raise KeyError(f"Unknown rune contract: {rune_id}")
