from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema

from abx.report_manifest_diff_ledger import LEDGER_PATH, read_diff_history
from abx.reporting_cycle import now_utc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "ReportManifestChangeSummary.v1.json"
SUMMARY_PATH = ROOT / "out" / "reports" / "report_manifest.summary.latest.json"


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _summary_id(*, timestamp_utc: str, window_size: int, totals: dict[str, int], patterns: dict[str, int], stability_indicator: str) -> str:
    material = json.dumps(
        {
            "timestamp_utc": timestamp_utc,
            "window_size": window_size,
            "totals": totals,
            "patterns": patterns,
            "stability_indicator": stability_indicator,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _stability_indicator(*, computable: bool, totals: dict[str, int]) -> str:
    if not computable:
        return "NOT_COMPUTABLE"
    churn_score = (
        totals["added_total"]
        + totals["removed_total"]
        + totals["hash_changed_total"]
        + totals["freshness_changed_total"]
        + totals["status_changed_total"]
    )
    if churn_score <= 2:
        return "STABLE"
    if churn_score <= 8:
        return "MODERATE_CHURN"
    return "HIGH_CHURN"


def build_manifest_change_summary(*, window_size: int = 10, timestamp_utc: str | None = None) -> dict[str, Any]:
    ts = timestamp_utc or now_utc()
    bounded = max(1, min(int(window_size), 100))
    history_payload = read_diff_history(limit=bounded)
    history = history_payload.get("history") if isinstance(history_payload.get("history"), list) else []

    if not history:
        totals = {
            "added_total": 0,
            "removed_total": 0,
            "hash_changed_total": 0,
            "freshness_changed_total": 0,
            "status_changed_total": 0,
        }
        patterns = {
            "repeated_hash_churn_count": 0,
            "stale_transition_count": 0,
            "artifact_disappearance_count": 0,
        }
        indicator = "NOT_COMPUTABLE"
        summary = {
            "summary_id": _summary_id(
                timestamp_utc=ts,
                window_size=bounded,
                totals=totals,
                patterns=patterns,
                stability_indicator=indicator,
            ),
            "timestamp_utc": ts,
            "window_size": bounded,
            "totals": totals,
            "patterns": patterns,
            "stability_indicator": indicator,
            "provenance": {
                "source": "abx.report_manifest_summary.build_manifest_change_summary",
                "reason": str(history_payload.get("reason", f"report_missing:{LEDGER_PATH.as_posix()}")),
                "deterministic_ordering": [
                    "summary_id",
                    "timestamp_utc",
                    "window_size",
                    "totals",
                    "patterns",
                    "stability_indicator",
                    "provenance",
                ],
            },
        }
        jsonschema.Draft202012Validator(_load_schema()).validate(summary)
        return {
            "status": "NOT_COMPUTABLE",
            "reason": str(history_payload.get("reason", f"report_missing:{LEDGER_PATH.as_posix()}")),
            "summary": summary,
        }

    rows = [row for row in history if isinstance(row, dict)]
    totals = {
        "added_total": sum(int(row.get("added_count", 0) or 0) for row in rows),
        "removed_total": sum(int(row.get("removed_count", 0) or 0) for row in rows),
        "hash_changed_total": sum(int(row.get("hash_changed_count", 0) or 0) for row in rows),
        "freshness_changed_total": sum(int(row.get("freshness_changed_count", 0) or 0) for row in rows),
        "status_changed_total": sum(int(row.get("status_changed_count", 0) or 0) for row in rows),
    }

    repeated_hash_churn_count = sum(1 for row in rows if int(row.get("hash_changed_count", 0) or 0) > 0)
    stale_transition_count = totals["freshness_changed_total"]
    artifact_disappearance_count = totals["removed_total"]

    patterns = {
        "repeated_hash_churn_count": repeated_hash_churn_count,
        "stale_transition_count": stale_transition_count,
        "artifact_disappearance_count": artifact_disappearance_count,
    }

    indicator = _stability_indicator(computable=True, totals=totals)
    summary = {
        "summary_id": _summary_id(
            timestamp_utc=ts,
            window_size=bounded,
            totals=totals,
            patterns=patterns,
            stability_indicator=indicator,
        ),
        "timestamp_utc": ts,
        "window_size": bounded,
        "totals": totals,
        "patterns": patterns,
        "stability_indicator": indicator,
        "provenance": {
            "source": "abx.report_manifest_summary.build_manifest_change_summary",
            "reason": "ok",
            "history_records_considered": len(rows),
            "deterministic_ordering": [
                "summary_id",
                "timestamp_utc",
                "window_size",
                "totals",
                "patterns",
                "stability_indicator",
                "provenance",
            ],
        },
    }
    jsonschema.Draft202012Validator(_load_schema()).validate(summary)
    return {
        "status": "OK",
        "reason": "ok",
        "summary": summary,
    }


def write_manifest_change_summary(payload: dict[str, Any], path: Path = SUMMARY_PATH) -> None:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def read_manifest_change_summary(path: Path = SUMMARY_PATH) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "NOT_COMPUTABLE",
            "reason": f"report_missing:{path.as_posix()}",
            "summary": None,
        }
    summary = json.loads(path.read_text(encoding="utf-8"))
    indicator = str(summary.get("stability_indicator", "NOT_COMPUTABLE")) if isinstance(summary, dict) else "NOT_COMPUTABLE"
    return {
        "status": "OK" if indicator != "NOT_COMPUTABLE" else "NOT_COMPUTABLE",
        "reason": str((summary.get("provenance") if isinstance(summary, dict) else {}).get("reason", "ok")),
        "summary": summary,
    }
