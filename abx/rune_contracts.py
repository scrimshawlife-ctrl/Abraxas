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


def _category_for_layer(layer: str) -> str:
    normalized = (layer or "").strip().lower()
    if normalized in {"ingest", "input", "acquire"}:
        return "INGEST"
    if normalized in {"governance", "validation"}:
        return "VALIDATE"
    if normalized in {"core"}:
        return "DETECT"
    return "ENFORCE"


def load_abx_rune_contracts(registry_path: Path | None = None) -> list[ABXRuneContract]:
    payload = _load_registry_payload(registry_path)
    contracts: list[ABXRuneContract] = []

    for entry in payload.get("runes", []):
        definition_path = _repo_root() / entry["definition_path"]
        definition = RuneDefinition(**json.loads(definition_path.read_text(encoding="utf-8")))
        metadata = definition.metadata if isinstance(definition.metadata, dict) else {}
        dependencies = metadata.get("dependencies") if isinstance(metadata.get("dependencies"), list) else []
        lane = str(metadata.get("lane", "ACTIVE")).upper()
        if lane not in {"ACTIVE", "SHADOW", "CANARY", "DEPRECATED"}:
            lane = "ACTIVE"

        contracts.append(
            ABXRuneContract(
                rune_id=definition.id,
                acronym=definition.short_name,
                version=definition.introduced_version,
                lane=lane,
                category=_category_for_layer(definition.layer),
                inputs=[ABXRuneIO(name=name, type="object", required=True) for name in definition.inputs],
                outputs=[ABXRuneOutput(name=name, type="object") for name in definition.outputs],
                dependencies=[str(dep) for dep in dependencies],
                influence_policy="BOUNDED",
                determinism_rule="identical_input_identical_output_no_randomness_no_time_variation",
                provenance_fields=["run_id", "rune_id", "artifact_id"],
                failure_modes=["stub_blocked", "execution_failed", "schema_validation_failed"],
            )
        )

    return sorted(contracts, key=lambda c: c.rune_id)
