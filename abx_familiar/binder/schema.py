"""Validate FamiliarBinding.v0 dicts.

Uses jsonschema when installed. Otherwise checks required fields locally
against the same rules as contracts/familiar/familiar_binding.v0.schema.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "familiar"
    / "familiar_binding.v0.schema.json"
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = (
    "schema_version",
    "binding_id",
    "status",
    "lane",
    "advisory_only",
    "authority",
    "pack_id",
    "pack_hash",
    "receipt_id",
    "receipt_hash",
    "ward_pre_id",
    "ward_pre_hash",
    "blockers",
    "binding_hash",
)


def load_binding_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _local_errors(binding: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in binding:
            errors.append(f"missing {key}")
    if binding.get("schema_version") != "FamiliarBinding.v0":
        errors.append("schema_version")
    if binding.get("status") not in {"BOUND_SHADOW", "BIND_REJECTED"}:
        errors.append("status")
    if binding.get("lane") != "SHADOW":
        errors.append("lane")
    if binding.get("advisory_only") is not True:
        errors.append("advisory_only")
    auth = binding.get("authority") if isinstance(binding.get("authority"), dict) else {}
    for field in (
        "execution_authority",
        "promotion_authorized",
        "forecast_routing_authorized",
        "canon_mutation_allowed",
    ):
        if auth.get(field) is not False:
            errors.append(field)
    for hex_key in ("pack_hash", "ward_pre_hash", "binding_hash"):
        if not HEX64.match(str(binding.get(hex_key, ""))):
            errors.append(hex_key)
    if not isinstance(binding.get("blockers"), list):
        errors.append("blockers")
    return errors


def validate_binding(binding: dict[str, Any]) -> list[str]:
    try:
        from jsonschema import Draft7Validator
    except ImportError:
        return _local_errors(binding)
    validator = Draft7Validator(load_binding_schema())
    return sorted(e.message for e in validator.iter_errors(binding))
