from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema

from abx.report_freshness import evaluate_freshness
from abx.reporting_cycle import now_utc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "ReportManifestRecord.v1.json"
LATEST_PATH = ROOT / "out" / "reports" / "report_manifest.latest.json"

ARTIFACT_SPECS: list[dict[str, str]] = [
    {
        "artifact_type": "developer_readiness",
        "path": "out/reports/developer_readiness.json",
        "source_command": "python scripts/run_developer_readiness.py",
    },
    {
        "artifact_type": "invariance",
        "path": "out/reports/gap_closure_invariance.projection.json",
        "source_command": "python scripts/project_gap_closure_invariance.py",
    },
    {
        "artifact_type": "comparison",
        "path": "out/reports/readiness_comparison.latest.json",
        "source_command": "python scripts/log_readiness_comparison.py",
    },
    {
        "artifact_type": "preflight",
        "path": "out/reports/promotion_preflight.latest.json",
        "source_command": "python scripts/generate_promotion_preflight.py",
    },
    {
        "artifact_type": "reporting_cycle",
        "path": "out/reports/reporting_cycle.latest.json",
        "source_command": "python scripts/run_reporting_cycle.py",
    },
]


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extract_timestamp(artifact_type: str, payload: dict[str, Any]) -> str | None:
    if artifact_type in {"developer_readiness", "comparison", "preflight", "reporting_cycle"}:
        value = payload.get("timestamp_utc")
        return str(value) if value else None
    if artifact_type == "invariance":
        provenance = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}
        value = provenance.get("projection_generated_at")
        return str(value) if value else None
    return None


def _artifact_id(*, artifact_type: str, path: str, timestamp_utc: str, digest: str, status: str) -> str:
    material = json.dumps(
        {
            "artifact_type": artifact_type,
            "path": path,
            "timestamp_utc": timestamp_utc,
            "hash": digest,
            "status": status,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_report_manifest(*, current_time_utc: str | None = None) -> list[dict[str, Any]]:
    ts_now = current_time_utc or now_utc()
    schema = _load_schema()
    records: list[dict[str, Any]] = []

    for spec in ARTIFACT_SPECS:
        artifact_type = spec["artifact_type"]
        rel_path = spec["path"]
        path = ROOT / rel_path

        if not path.exists():
            freshness = evaluate_freshness(None, ts_now, artifact_type=artifact_type)
            record = {
                "artifact_id": _artifact_id(
                    artifact_type=artifact_type,
                    path=rel_path,
                    timestamp_utc="NOT_COMPUTABLE",
                    digest="NOT_COMPUTABLE",
                    status="NOT_COMPUTABLE",
                ),
                "artifact_type": artifact_type,
                "path": rel_path,
                "timestamp_utc": "NOT_COMPUTABLE",
                "freshness": {
                    "is_stale": bool(freshness["is_stale"]),
                    "age_seconds": int(freshness["age_seconds"]),
                },
                "hash": "NOT_COMPUTABLE",
                "source_command": spec["source_command"],
                "provenance": {
                    "source": "abx.report_manifest.build_report_manifest",
                    "status": "NOT_COMPUTABLE",
                    "reason": f"report_missing:{path.as_posix()}",
                    "deterministic_ordering": [
                        "artifact_id",
                        "artifact_type",
                        "path",
                        "timestamp_utc",
                        "freshness",
                        "hash",
                        "source_command",
                        "provenance",
                    ],
                },
            }
            jsonschema.Draft202012Validator(schema).validate(record)
            records.append(record)
            continue

        payload = json.loads(path.read_text(encoding="utf-8"))
        timestamp_utc = _extract_timestamp(artifact_type, payload) or "NOT_COMPUTABLE"
        freshness = evaluate_freshness(
            None if timestamp_utc == "NOT_COMPUTABLE" else timestamp_utc,
            ts_now,
            artifact_type=artifact_type,
        )
        digest = _file_hash(path)
        record = {
            "artifact_id": _artifact_id(
                artifact_type=artifact_type,
                path=rel_path,
                timestamp_utc=timestamp_utc,
                digest=digest,
                status="OK",
            ),
            "artifact_type": artifact_type,
            "path": rel_path,
            "timestamp_utc": timestamp_utc,
            "freshness": {
                "is_stale": bool(freshness["is_stale"]),
                "age_seconds": int(freshness["age_seconds"]),
            },
            "hash": digest,
            "source_command": spec["source_command"],
            "provenance": {
                "source": "abx.report_manifest.build_report_manifest",
                "status": "OK" if freshness.get("status") == "OK" else "NOT_COMPUTABLE",
                "freshness_reason": str(freshness.get("reason", "unknown")),
                "deterministic_ordering": [
                    "artifact_id",
                    "artifact_type",
                    "path",
                    "timestamp_utc",
                    "freshness",
                    "hash",
                    "source_command",
                    "provenance",
                ],
            },
        }
        jsonschema.Draft202012Validator(schema).validate(record)
        records.append(record)

    records.sort(key=lambda row: str(row.get("artifact_type", "")))
    return records


def write_report_manifest(records: list[dict[str, Any]], path: Path = LATEST_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def read_report_manifest(path: Path = LATEST_PATH) -> dict[str, Any]:
    if not path.exists():
        records = build_report_manifest()
        return {
            "status": "OK",
            "reason": "ok",
            "manifest": records,
        }
    records = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": "OK",
        "reason": "ok",
        "manifest": records,
    }
