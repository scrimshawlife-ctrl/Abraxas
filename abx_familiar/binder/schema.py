"""Validate FamiliarBinding.v0 dicts against the repo schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "familiar"
    / "familiar_binding.v0.schema.json"
)


def load_binding_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_binding(binding: dict[str, Any]) -> list[str]:
    validator = Draft7Validator(load_binding_schema())
    return sorted(e.message for e in validator.iter_errors(binding))
