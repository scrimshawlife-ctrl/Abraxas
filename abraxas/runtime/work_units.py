"""Deterministic work unit definitions for parallel stages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from abraxas.core.canonical import canonical_json, sha256_hex


@dataclass(frozen=True)
class WorkUnit:
    unit_id: str
    stage: str
    source_id: str
    window_utc: Dict[str, str | None]
    key: Tuple[Any, ...]
    input_refs: Dict[str, Any]
    output_refs: Dict[str, Any] | None = None
    input_bytes: int = 0

    @classmethod
    def build(
        cls,
        *,
        stage: str,
        source_id: str,
        window_utc: Dict[str, str | None],
        key: Tuple[Any, ...],
        input_refs: Dict[str, Any],
        input_bytes: int = 0,
    ) -> "WorkUnit":
        payload = {
            "stage": stage,
            "source_id": source_id,
            "window_utc": window_utc,
            "key": key,
            "input_refs": input_refs,
        }
        unit_id = sha256_hex(canonical_json(payload))
        return cls(
            unit_id=unit_id,
            stage=stage,
            source_id=source_id,
            window_utc=window_utc,
            key=key,
            input_refs=input_refs,
            output_refs=None,
            input_bytes=input_bytes,
        )
