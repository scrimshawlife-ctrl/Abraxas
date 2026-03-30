from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def _required_fields() -> tuple[str, ...]:
    schema_path = Path("aal_core/schemas/large_run_execution_artifact.v1.json")
    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    required = payload.get("required", [])
    return tuple(str(item) for item in required if str(item))


def validate_large_run_envelope(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in _required_fields():
        if field not in payload:
            issues.append(f"missing:{field}")

    if "run_id" in payload and not str(payload.get("run_id", "")).startswith("BATCH::"):
        issues.append("invalid:run_id")
    if "correlation_pointers" in payload and not isinstance(payload.get("correlation_pointers"), list):
        issues.append("invalid:correlation_pointers")
    if "provenance" in payload:
        provenance = payload.get("provenance")
        if not isinstance(provenance, dict) or not isinstance(provenance.get("builder"), str) or not provenance.get("builder"):
            issues.append("invalid:provenance.builder")
    return sorted(issues)


def assert_large_run_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    issues = validate_large_run_envelope(payload)
    if issues:
        raise ValueError("invalid large-run envelope: " + ", ".join(issues))
    return payload
