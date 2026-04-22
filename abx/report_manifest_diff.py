from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema

from abx.report_manifest import LATEST_PATH as MANIFEST_LATEST_PATH, build_report_manifest, write_report_manifest
from abx.reporting_cycle import now_utc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "ReportManifestDiff.v1.json"
DIFF_LATEST_PATH = ROOT / "out" / "reports" / "report_manifest.diff.latest.json"
PREVIOUS_PATH = ROOT / "out" / "reports" / "report_manifest.previous.json"


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _diff_id(*, timestamp_utc: str, added: list[str], removed: list[str], hash_changed: list[str], freshness_changed: list[str], status_changed: list[str], unchanged_count: int, status: str) -> str:
    material = json.dumps(
        {
            "timestamp_utc": timestamp_utc,
            "added": sorted(added),
            "removed": sorted(removed),
            "hash_changed": sorted(hash_changed),
            "freshness_changed": sorted(freshness_changed),
            "status_changed": sorted(status_changed),
            "unchanged_count": int(unchanged_count),
            "status": status,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _artifact_key(row: dict[str, Any]) -> str:
    return str(row.get("artifact_type", ""))


def build_report_manifest_diff(*, current_manifest: list[dict[str, Any]], previous_manifest: list[dict[str, Any]] | None, timestamp_utc: str | None = None) -> dict[str, Any]:
    ts = timestamp_utc or now_utc()
    schema = _load_schema()

    if previous_manifest is None:
        diff = {
            "diff_id": _diff_id(
                timestamp_utc=ts,
                added=[],
                removed=[],
                hash_changed=[],
                freshness_changed=[],
                status_changed=[],
                unchanged_count=0,
                status="NOT_COMPUTABLE",
            ),
            "timestamp_utc": ts,
            "added": [],
            "removed": [],
            "hash_changed": [],
            "freshness_changed": [],
            "status_changed": [],
            "unchanged_count": 0,
            "provenance": {
                "source": "abx.report_manifest_diff.build_report_manifest_diff",
                "status": "NOT_COMPUTABLE",
                "reason": f"previous_manifest_missing:{PREVIOUS_PATH.as_posix()}",
                "deterministic_ordering": [
                    "diff_id",
                    "timestamp_utc",
                    "added",
                    "removed",
                    "hash_changed",
                    "freshness_changed",
                    "status_changed",
                    "unchanged_count",
                    "provenance",
                ],
            },
        }
        jsonschema.Draft202012Validator(schema).validate(diff)
        return {
            "status": "NOT_COMPUTABLE",
            "reason": f"previous_manifest_missing:{PREVIOUS_PATH.as_posix()}",
            "diff": diff,
        }

    current_by_key = {_artifact_key(row): row for row in current_manifest if isinstance(row, dict)}
    previous_by_key = {_artifact_key(row): row for row in previous_manifest if isinstance(row, dict)}

    current_ids = {str(row.get("artifact_id", "")) for row in current_manifest if isinstance(row, dict)}
    previous_ids = {str(row.get("artifact_id", "")) for row in previous_manifest if isinstance(row, dict)}

    added = sorted(current_ids - previous_ids)
    removed = sorted(previous_ids - current_ids)

    common_keys = sorted(set(current_by_key.keys()) & set(previous_by_key.keys()))
    added_artifact_types = sorted(set(current_by_key.keys()) - set(previous_by_key.keys()))
    removed_artifact_types = sorted(set(previous_by_key.keys()) - set(current_by_key.keys()))
    hash_changed: list[str] = []
    freshness_changed: list[str] = []
    status_changed: list[str] = []
    unchanged_count = 0

    for key in common_keys:
        current_row = current_by_key[key]
        previous_row = previous_by_key[key]

        current_hash = str(current_row.get("hash", ""))
        previous_hash = str(previous_row.get("hash", ""))
        if current_hash != previous_hash:
            hash_changed.append(key)

        current_stale = bool((current_row.get("freshness") if isinstance(current_row.get("freshness"), dict) else {}).get("is_stale", True))
        previous_stale = bool((previous_row.get("freshness") if isinstance(previous_row.get("freshness"), dict) else {}).get("is_stale", True))
        if current_stale != previous_stale:
            freshness_changed.append(key)

        current_status = str((current_row.get("provenance") if isinstance(current_row.get("provenance"), dict) else {}).get("status", "NOT_COMPUTABLE"))
        previous_status = str((previous_row.get("provenance") if isinstance(previous_row.get("provenance"), dict) else {}).get("status", "NOT_COMPUTABLE"))
        if current_status != previous_status:
            status_changed.append(key)

        if current_hash == previous_hash and current_stale == previous_stale and current_status == previous_status:
            unchanged_count += 1

    diff = {
        "diff_id": _diff_id(
            timestamp_utc=ts,
            added=added,
            removed=removed,
            hash_changed=hash_changed,
            freshness_changed=freshness_changed,
            status_changed=status_changed,
            unchanged_count=unchanged_count,
            status="OK",
        ),
        "timestamp_utc": ts,
        "added": added,
        "removed": removed,
        "added_artifact_types": added_artifact_types,
        "removed_artifact_types": removed_artifact_types,
        "hash_changed": sorted(hash_changed),
        "freshness_changed": sorted(freshness_changed),
        "status_changed": sorted(status_changed),
        "unchanged_count": unchanged_count,
        "provenance": {
            "source": "abx.report_manifest_diff.build_report_manifest_diff",
            "status": "OK",
            "reason": "ok",
            "comparison_mode": "artifact_id_added_removed_with_artifact_type_delta_checks",
            "deterministic_ordering": [
                "diff_id",
                "timestamp_utc",
                "added",
                "removed",
                "hash_changed",
                "freshness_changed",
                "status_changed",
                "unchanged_count",
                "provenance",
            ],
        },
    }
    jsonschema.Draft202012Validator(schema).validate(diff)
    return {
        "status": "OK",
        "reason": "ok",
        "diff": diff,
    }


def generate_report_manifest_diff() -> dict[str, Any]:
    current_manifest = build_report_manifest()
    write_report_manifest(current_manifest, MANIFEST_LATEST_PATH)

    previous_manifest: list[dict[str, Any]] | None = None
    if PREVIOUS_PATH.exists():
        loaded = json.loads(PREVIOUS_PATH.read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            previous_manifest = [row for row in loaded if isinstance(row, dict)]

    payload = build_report_manifest_diff(current_manifest=current_manifest, previous_manifest=previous_manifest)
    DIFF_LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    DIFF_LATEST_PATH.write_text(json.dumps(payload.get("diff"), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    PREVIOUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREVIOUS_PATH.write_text(json.dumps(current_manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return payload


def read_report_manifest_diff(path: Path = DIFF_LATEST_PATH) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "NOT_COMPUTABLE",
            "reason": f"report_missing:{path.as_posix()}",
            "diff": None,
        }
    diff = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": str((diff.get("provenance") if isinstance(diff.get("provenance"), dict) else {}).get("status", "OK")),
        "reason": str((diff.get("provenance") if isinstance(diff.get("provenance"), dict) else {}).get("reason", "ok")),
        "diff": diff,
    }
