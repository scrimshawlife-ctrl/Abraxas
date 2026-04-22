from __future__ import annotations

import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = ROOT / "out" / "reports" / "developer_readiness.json"
PROJECTION_SCHEMA_PATH = ROOT / "schemas" / "DeveloperReadinessProjection.v1.json"

_ORDERED_CHECK_FIELDS = (
    "check_id",
    "label",
    "command",
    "status",
    "return_code",
    "missing_files",
)


def _stable_sort_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {key: value[key] for key in sorted(value.keys())}


def _normalize_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in checks:
        packet = {
            "check_id": str(row.get("check_id", "")),
            "label": str(row.get("label", "")),
            "command": str(row.get("command", "")),
            "status": str(row.get("status", "NOT_COMPUTABLE")),
            "return_code": row.get("return_code", None),
            "missing_files": sorted(str(item) for item in row.get("missing_files", []) if str(item)),
        }
        normalized.append(packet)
    return sorted(normalized, key=lambda item: item["check_id"])


def _derive_input_hash(checks: list[dict[str, Any]]) -> str:
    material = "\n".join(
        "|".join(str(check.get(field, "")) for field in _ORDERED_CHECK_FIELDS)
        for check in _normalize_checks(checks)
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _environment_marker() -> dict[str, str]:
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cwd": str(ROOT),
        "ci": "true" if os.getenv("CI") else "false",
    }


def project_developer_readiness(raw: dict[str, Any]) -> dict[str, Any]:
    checks = raw.get("checks") if isinstance(raw.get("checks"), list) else []
    normalized = {
        "run_id": str(raw.get("run_id", "")),
        "timestamp_utc": str(raw.get("timestamp_utc", "")),
        "status": str(raw.get("status", "NOT_COMPUTABLE")),
        "checks": _normalize_checks([row for row in checks if isinstance(row, dict)]),
        "missing_surfaces": sorted(
            [
                _stable_sort_dict(
                    {
                        "check_id": str(row.get("check_id", "")),
                        "missing_files": sorted(str(item) for item in row.get("missing_files", []) if str(item)),
                    }
                )
                for row in raw.get("missing_surfaces", [])
                if isinstance(row, dict)
            ],
            key=lambda item: item["check_id"],
        ),
        "recommended_next_actions": sorted(
            str(item) for item in raw.get("recommended_next_actions", []) if str(item)
        ),
        "provenance": _stable_sort_dict(
            {
                **(raw.get("provenance") if isinstance(raw.get("provenance"), dict) else {}),
                "input_hash": _derive_input_hash([row for row in checks if isinstance(row, dict)]),
                "execution_environment": _environment_marker(),
                "deterministic_ordering": [item["check_id"] for item in _normalize_checks([row for row in checks if isinstance(row, dict)])],
                "projection_generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            }
        ),
    }
    with PROJECTION_SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    jsonschema.Draft202012Validator(schema).validate(normalized)
    return normalized


def read_developer_readiness_payload(report_path: Path = DEFAULT_REPORT_PATH) -> dict[str, Any]:
    if not report_path.exists():
        return {
            "status": "NOT_COMPUTABLE",
            "reason": f"report_missing:{report_path.as_posix()}",
            "raw": None,
            "projection": {
                "run_id": "NOT_COMPUTABLE",
                "timestamp_utc": "NOT_COMPUTABLE",
                "status": "NOT_COMPUTABLE",
                "checks": [],
                "missing_surfaces": [],
                "recommended_next_actions": [
                    "Run make developer-readiness to generate out/reports/developer_readiness.json"
                ],
                "provenance": {
                    "source": "abx.developer_readiness.read_developer_readiness_payload",
                    "input_hash": "NOT_COMPUTABLE",
                    "execution_environment": _environment_marker(),
                    "deterministic_ordering": [],
                    "projection_generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                },
            },
        }

    raw = json.loads(report_path.read_text(encoding="utf-8"))
    projection = project_developer_readiness(raw)
    return {
        "status": projection.get("status", "NOT_COMPUTABLE"),
        "reason": "ok",
        "raw": raw,
        "projection": projection,
    }
