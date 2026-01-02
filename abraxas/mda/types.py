from __future__ import annotations

from typing import Any

from abraxas.core.canonical import canonical_json, sha256_hex


def stable_json_dumps(obj: Any) -> str:
    """
    Deterministic JSON serialization for hashing/provenance.

    This intentionally matches `abraxas.core.canonical.canonical_json`:
    - sorted keys
    - stable separators
    - UTF-8 / ensure_ascii=False
    """

    return canonical_json(obj)


__all__ = ["sha256_hex", "stable_json_dumps"]

