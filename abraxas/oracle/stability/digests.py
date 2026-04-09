from __future__ import annotations

from typing import Any, Mapping

from abraxas.core.canonical import sha256_hex
from abraxas.oracle.stability.canonicalize import canonical_authority_blob, canonical_full_blob, canonical_input_blob


def compute_digest_triplet(*, normalized: Mapping[str, Any], output: Mapping[str, Any]) -> dict[str, str]:
    return {
        "input_hash": sha256_hex(canonical_input_blob(normalized)),
        "authority_hash": sha256_hex(canonical_authority_blob(output)),
        "full_hash": sha256_hex(canonical_full_blob(output)),
    }
