from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate


class ContractLoadError(ValueError):
    def __init__(self, reason: str, path: str, expected_schema_version: str) -> None:
        self.reason = reason
        self.path = path
        self.expected_schema_version = expected_schema_version
        super().__init__(f"{reason}:{path}:{expected_schema_version}")


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def attach_canonical_hash(contract: dict[str, Any]) -> dict[str, Any]:
    payload = {k: v for k, v in contract.items() if k != "canonical_hash"}
    out = dict(payload)
    out["canonical_hash"] = canonical_hash(payload)
    return out


def validate_canonical_hash(contract: dict[str, Any]) -> bool:
    expected = canonical_hash({k: v for k, v in contract.items() if k != "canonical_hash"})
    return contract.get("canonical_hash") == expected


def validate_schema_version(contract: dict[str, Any], expected_schema_version: str) -> bool:
    return contract.get("schema_version") == expected_schema_version


def validate_against_schema(contract: dict[str, Any], schema_path: str | Path) -> bool:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    envelope_required = "envelope" in contract
    validate(instance=contract, schema=schema)
    if envelope_required:
        envelope_schema = json.loads(Path("schemas/SemanticEnvelope.v1.schema.json").read_text(encoding="utf-8"))
        validate(instance=contract["envelope"], schema=envelope_schema)
    return True


def _schema_path_for(expected_schema_version: str) -> Path:
    return Path("schemas") / f"{expected_schema_version}.schema.json"


def load_contract(path: str | Path, expected_schema_version: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise ContractLoadError("MISSING_INPUT", p.as_posix(), expected_schema_version)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ContractLoadError("INVALID_JSON", p.as_posix(), expected_schema_version) from exc
    if not isinstance(data, dict):
        raise ContractLoadError("INVALID_CONTRACT", p.as_posix(), expected_schema_version)
    if not validate_schema_version(data, expected_schema_version):
        raise ContractLoadError("INVALID_SCHEMA_VERSION", p.as_posix(), expected_schema_version)
    try:
        validate_against_schema(data, _schema_path_for(expected_schema_version))
    except (ValidationError, FileNotFoundError, json.JSONDecodeError):
        raise ContractLoadError("INVALID_SCHEMA", p.as_posix(), expected_schema_version)
    if not validate_canonical_hash(data):
        raise ContractLoadError("INVALID_CANONICAL_HASH", p.as_posix(), expected_schema_version)
    return data
