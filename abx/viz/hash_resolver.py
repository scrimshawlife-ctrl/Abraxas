from __future__ import annotations

from typing import Any, Mapping


def resolve_source_hash(path: str, artifact: Mapping[str, Any] | None = None) -> str:
    data = artifact or {}
    hash_value = data.get("sha256")
    if isinstance(hash_value, str) and hash_value.strip():
        return hash_value.strip()
    return "NOT_COMPUTABLE"
