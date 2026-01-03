"""Emit deterministic seedpack v0.2 from frames and reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from abraxas.core.canonical import canonical_json, sha256_hex

SEEDPACK_SCHEMA_VERSION = "seedpack.v0.2"


def emit_seedpack(
    *,
    year: int,
    frames: List[Dict[str, Any]],
    influence: Dict[str, Any],
    synchronicity: Dict[str, Any],
    out_path: Path,
) -> Dict[str, Any]:
    payload = {
        "schema_version": SEEDPACK_SCHEMA_VERSION,
        "year": year,
        "frames": frames,
        "influence": influence,
        "synchronicity": synchronicity,
    }
    payload["seedpack_hash"] = sha256_hex(canonical_json(payload))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload
