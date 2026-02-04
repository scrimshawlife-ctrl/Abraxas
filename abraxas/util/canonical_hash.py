from __future__ import annotations

from typing import Any
import hashlib
import json


class CanonicalHashError(ValueError):
    pass


def _canonicalize(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, float):
        raise CanonicalHashError("Floats are forbidden in canonical hashing.")
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, dict):
        out = {}
        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise CanonicalHashError("Only string keys are allowed in canonical hashing.")
            out[key] = _canonicalize(value[key])
        return out
    raise CanonicalHashError(f"Unsupported type for canonical hashing: {type(value).__name__}")


def canonical_json_bytes(payload: Any) -> bytes:
    canonical = _canonicalize(payload)
    stable = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return stable.encode("utf-8")


def canonical_json_str(payload: Any) -> str:
    return canonical_json_bytes(payload).decode("utf-8")


def canonical_hash(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
