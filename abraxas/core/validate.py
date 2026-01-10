from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple, List

import jsonschema

from .logging import stable_hash


@dataclass(frozen=True)
class ValidationErrorDetail:
    path: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    schema_id: str
    payload_hash: str
    errors: Tuple[ValidationErrorDetail, ...] = ()


class SchemaRegistry:
    """
    Deterministic schema loading. No network. No remote refs.
    """
    def __init__(self, schemas_root: Path):
        self.root = schemas_root

    def load(self, filename: str) -> Dict[str, Any]:
        p = (self.root / filename).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Schema not found: {p}")
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)

    def resolve_ref(self, ref: str) -> Dict[str, Any]:
        # Only allow local file refs like "common.v0.json#/definitions/X"
        if "://" in ref:
            raise ValueError("Remote schema refs are forbidden.")
        file_part = ref.split("#", 1)[0]
        if not file_part:
            raise ValueError(f"Unsupported $ref: {ref}")
        return self.load(file_part)


def validate_payload(
    schemas: SchemaRegistry,
    schema_filename: str,
    payload: Dict[str, Any],
) -> ValidationResult:
    h = stable_hash(payload)
    schema = schemas.load(schema_filename)
    schema_id = schema.get("$id", schema_filename)

    resolver = jsonschema.RefResolver(
        base_uri="file://" + str(schemas.root.resolve()) + "/",
        referrer=schema,
        handlers={"file": lambda uri: schemas.load(Path(uri.replace("file://", "")).name)},
    )

    validator = jsonschema.Draft202012Validator(schema, resolver=resolver)
    errs: List[ValidationErrorDetail] = []
    for e in sorted(validator.iter_errors(payload), key=lambda x: list(x.path)):
        p = "$" + "".join([f"[{repr(x)}]" if isinstance(x, int) else f".{x}" for x in e.path])
        errs.append(ValidationErrorDetail(path=p, message=e.message))

    return ValidationResult(
        ok=(len(errs) == 0),
        schema_id=schema_id,
        payload_hash=h,
        errors=tuple(errs),
    )


# --- Tier visibility enforcement (schema-level gate) ---

_TIER_ORDER = {"psychonaut": 0, "academic": 1, "enterprise": 2}


def tier_allows(viewer_tier: str, item_tier: str) -> bool:
    return _TIER_ORDER[viewer_tier] >= _TIER_ORDER[item_tier]


def redact_by_tier(viewer_tier: str, obj: Any) -> Any:
    """
    Deterministic redaction:
    - If an object contains `tier_visibility`, enforce it.
    - Recursively process lists/dicts.
    """
    if isinstance(obj, list):
        out = []
        for item in obj:
            redacted = redact_by_tier(viewer_tier, item)
            if redacted is not None:
                out.append(redacted)
        return out

    if isinstance(obj, dict):
        if "tier_visibility" in obj:
            tv = obj.get("tier_visibility")
            if isinstance(tv, str) and tv in _TIER_ORDER:
                if not tier_allows(viewer_tier, tv):
                    return None
        out = {}
        for k in sorted(obj.keys()):
            v = redact_by_tier(viewer_tier, obj[k])
            if v is not None:
                out[k] = v
        return out

    return obj
