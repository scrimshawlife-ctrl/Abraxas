from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema

from abx.report_manifest_diff import DIFF_LATEST_PATH, read_report_manifest_diff
from abx.reporting_cycle import now_utc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "ReportManifestDiffLedgerRecord.v1.json"
LEDGER_PATH = ROOT / "out" / "reports" / "report_manifest.diff.ledger.jsonl"


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _ledger_entry_id(*, diff_id: str, timestamp_utc: str, status: str, counts: dict[str, int]) -> str:
    material = json.dumps(
        {
            "diff_id": diff_id,
            "timestamp_utc": timestamp_utc,
            "status": status,
            "counts": counts,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_ledger_record(*, diff_payload: dict[str, Any] | None) -> dict[str, Any]:
    schema = _load_schema()
    if not diff_payload or not isinstance(diff_payload.get("diff"), dict):
        ts = now_utc()
        counts = {
            "added_count": 0,
            "removed_count": 0,
            "hash_changed_count": 0,
            "freshness_changed_count": 0,
            "status_changed_count": 0,
            "unchanged_count": 0,
        }
        record = {
            "ledger_entry_id": _ledger_entry_id(diff_id="NOT_COMPUTABLE", timestamp_utc=ts, status="NOT_COMPUTABLE", counts=counts),
            "diff_id": "NOT_COMPUTABLE",
            "timestamp_utc": ts,
            **counts,
            "status": "NOT_COMPUTABLE",
            "artifact_events": [],
            "provenance": {
                "source": "abx.report_manifest_diff_ledger.build_ledger_record",
                "reason": f"latest_diff_missing:{DIFF_LATEST_PATH.as_posix()}",
                "deterministic_ordering": [
                    "ledger_entry_id",
                    "diff_id",
                    "timestamp_utc",
                    "added_count",
                    "removed_count",
                    "hash_changed_count",
                    "freshness_changed_count",
                    "status_changed_count",
                    "unchanged_count",
                    "status",
                    "artifact_events",
                    "provenance",
                ],
            },
        }
        jsonschema.Draft202012Validator(schema).validate(record)
        return record

    diff = diff_payload["diff"]
    diff_id = str(diff.get("diff_id", "NOT_COMPUTABLE"))
    ts = str(diff.get("timestamp_utc", now_utc()))
    counts = {
        "added_count": len(diff.get("added", [])) if isinstance(diff.get("added"), list) else 0,
        "removed_count": len(diff.get("removed", [])) if isinstance(diff.get("removed"), list) else 0,
        "hash_changed_count": len(diff.get("hash_changed", [])) if isinstance(diff.get("hash_changed"), list) else 0,
        "freshness_changed_count": len(diff.get("freshness_changed", [])) if isinstance(diff.get("freshness_changed"), list) else 0,
        "status_changed_count": len(diff.get("status_changed", [])) if isinstance(diff.get("status_changed"), list) else 0,
        "unchanged_count": int(diff.get("unchanged_count", 0) or 0),
    }
    status = str(diff_payload.get("status", "NOT_COMPUTABLE"))
    event_map: dict[str, dict[str, int | str]] = {}

    def _event_row(artifact_type: str) -> dict[str, int | str]:
        if artifact_type not in event_map:
            event_map[artifact_type] = {
                "artifact_type": artifact_type,
                "hash_changed_count": 0,
                "freshness_changed_count": 0,
                "status_changed_count": 0,
                "removed_count": 0,
            }
        return event_map[artifact_type]

    for artifact_type in diff.get("hash_changed", []) if isinstance(diff.get("hash_changed"), list) else []:
        row = _event_row(str(artifact_type))
        row["hash_changed_count"] = int(row["hash_changed_count"]) + 1

    for artifact_type in diff.get("freshness_changed", []) if isinstance(diff.get("freshness_changed"), list) else []:
        row = _event_row(str(artifact_type))
        row["freshness_changed_count"] = int(row["freshness_changed_count"]) + 1

    for artifact_type in diff.get("status_changed", []) if isinstance(diff.get("status_changed"), list) else []:
        row = _event_row(str(artifact_type))
        row["status_changed_count"] = int(row["status_changed_count"]) + 1

    removed_artifact_types = diff.get("removed_artifact_types", []) if isinstance(diff.get("removed_artifact_types"), list) else []
    if removed_artifact_types:
        for artifact_type in removed_artifact_types:
            row = _event_row(str(artifact_type))
            row["removed_count"] = int(row["removed_count"]) + 1
    elif counts["removed_count"] > 0:
        row = _event_row("UNKNOWN")
        row["removed_count"] = int(row["removed_count"]) + counts["removed_count"]

    artifact_events = [event_map[key] for key in sorted(event_map.keys())]
    record = {
        "ledger_entry_id": _ledger_entry_id(diff_id=diff_id, timestamp_utc=ts, status=status, counts=counts),
        "diff_id": diff_id,
        "timestamp_utc": ts,
        **counts,
        "status": status,
        "artifact_events": artifact_events,
        "provenance": {
            "source": "abx.report_manifest_diff_ledger.build_ledger_record",
            "reason": str(diff_payload.get("reason", "ok")),
            "deterministic_ordering": [
                "ledger_entry_id",
                "diff_id",
                "timestamp_utc",
                "added_count",
                "removed_count",
                "hash_changed_count",
                "freshness_changed_count",
                "status_changed_count",
                "unchanged_count",
                "status",
                "artifact_events",
                "provenance",
            ],
        },
    }
    jsonschema.Draft202012Validator(schema).validate(record)
    return record


def append_diff_ledger(record: dict[str, Any], ledger_path: Path = LEDGER_PATH) -> bool:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    diff_id = str(record.get("diff_id", ""))
    existing_ids: set[str] = set()
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            existing_ids.add(str(row.get("diff_id", "")))
    if diff_id and diff_id in existing_ids:
        return False
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return True


def log_diff_ledger() -> dict[str, Any]:
    diff_payload = read_report_manifest_diff()
    record = build_ledger_record(diff_payload=diff_payload)
    appended = append_diff_ledger(record)
    return {
        "status": "OK",
        "reason": "ok",
        "record": record,
        "appended": appended,
    }


def read_diff_history(*, limit: int = 20, ledger_path: Path = LEDGER_PATH) -> dict[str, Any]:
    bounded = max(1, min(int(limit), 100))
    if not ledger_path.exists():
        return {
            "status": "NOT_COMPUTABLE",
            "reason": f"report_missing:{ledger_path.as_posix()}",
            "history": [],
        }
    rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {
        "status": "OK",
        "reason": "ok",
        "history": rows[-bounded:],
    }
