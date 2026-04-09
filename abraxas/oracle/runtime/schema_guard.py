from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _schema_path(name: str) -> Path:
    return Path("schemas") / name


def _load_schema(name: str) -> dict[str, Any]:
    path = _schema_path(name)
    if not path.exists():
        raise ValueError(f"schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _manual_required_check(payload: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    required = list(schema.get("required") or [])
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"missing required keys: {sorted(missing)}")

    props = dict(schema.get("properties") or {})
    schema_prop = dict(props.get("schema_id") or {})
    const = schema_prop.get("const")
    if const is not None and payload.get("schema_id") != const:
        raise ValueError(f"schema_id must be {const}")

    # recurse only for inline object properties with direct required lists.
    for key, prop in props.items():
        if key not in payload:
            continue
        if not isinstance(prop, Mapping):
            continue
        if prop.get("type") != "object":
            continue
        nested = payload.get(key)
        if not isinstance(nested, Mapping):
            raise ValueError(f"{key} must be an object")
        nested_required = list(prop.get("required") or [])
        nested_missing = [rk for rk in nested_required if rk not in nested]
        if nested_missing:
            raise ValueError(f"missing required keys under {key}: {sorted(nested_missing)}")


def validate_payload_against_schema(payload: Mapping[str, Any], *, schema_name: str) -> None:
    schema = _load_schema(schema_name)
    _manual_required_check(payload, schema)


def validate_oslv2_input(payload: Mapping[str, Any]) -> None:
    validate_payload_against_schema(payload, schema_name="oracle_signal_input_envelope.v2.json")


def validate_oslv2_output(payload: Mapping[str, Any]) -> None:
    validate_payload_against_schema(payload, schema_name="oracle_signal_layer_output.v2.json")
