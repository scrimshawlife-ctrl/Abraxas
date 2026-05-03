from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json

from .subsystem_registry import load_subsystem_registry


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _path_exists_any(paths: list[str]) -> bool:
    return any(Path(path).exists() for path in paths)


@dataclass(frozen=True)
class SubsystemValidationResult:
    subsystem_id: str
    status: str  # PASS | FAIL | NOT_COMPUTABLE
    missing: list[str]


def validate_subsystem(row: dict[str, Any]) -> SubsystemValidationResult:
    subsystem_id = row["subsystem_id"]
    expected = row.get("expected_paths", {})
    if not isinstance(expected, dict):
        return SubsystemValidationResult(
            subsystem_id=subsystem_id,
            status="NOT_COMPUTABLE",
            missing=["expected_paths:invalid_type"],
        )

    missing: list[str] = []
    for category, paths in expected.items():
        if not isinstance(paths, list):
            return SubsystemValidationResult(
                subsystem_id=subsystem_id,
                status="NOT_COMPUTABLE",
                missing=[f"{category}:invalid_type"],
            )
        if not _path_exists_any(paths):
            missing.append(category)

    if missing:
        return SubsystemValidationResult(
            subsystem_id=subsystem_id,
            status="FAIL",
            missing=sorted(missing),
        )

    return SubsystemValidationResult(
        subsystem_id=subsystem_id,
        status="PASS",
        missing=[],
    )


def run_binding_validator() -> dict[str, Any]:
    registry = load_subsystem_registry()
    results: list[dict[str, Any]] = []
    pass_count = 0
    fail_count = 0
    not_computable_count = 0

    for row in registry.raw["subsystems"]:
        result = validate_subsystem(row)
        if result.status == "PASS":
            pass_count += 1
        elif result.status == "FAIL":
            fail_count += 1
        else:
            not_computable_count += 1
        results.append(
            {
                "subsystem_id": result.subsystem_id,
                "status": result.status,
                "missing": result.missing,
            }
        )

    overall_status = "PASS" if fail_count == 0 and not_computable_count == 0 else "FAIL"
    payload = {
        "schema_version": "BindingValidatorRun.v1",
        "registry_id": registry.registry_id,
        "overall_status": overall_status,
        "counts": {
            "total": len(results),
            "pass": pass_count,
            "fail": fail_count,
            "not_computable": not_computable_count,
        },
        "results": sorted(results, key=lambda item: item["subsystem_id"]),
    }
    payload_hash = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return {
        **payload,
        "canonical_hash": payload_hash,
        "authority": {
            "mutation": False,
            "promotion": False,
            "execution": False,
            "observe_only": True,
        },
    }
