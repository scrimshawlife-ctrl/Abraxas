from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema

from abx.report_manifest_diff_ledger import LEDGER_PATH, read_diff_history
from abx.reporting_cycle import now_utc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "ReportManifestWatchlist.v1.json"
WATCHLIST_PATH = ROOT / "out" / "reports" / "report_manifest.watchlist.latest.json"


THRESHOLDS = {
    "hash": 2,
    "freshness": 2,
    "removed": 2,
    "status": 2,
}


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _watchlist_id(*, timestamp_utc: str, items: list[dict[str, Any]]) -> str:
    material = json.dumps({"timestamp_utc": timestamp_utc, "items": items}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_report_manifest_watchlist(*, window_size: int = 20, timestamp_utc: str | None = None) -> dict[str, Any]:
    ts = timestamp_utc or now_utc()
    bounded = max(1, min(int(window_size), 100))
    payload = read_diff_history(limit=bounded)
    history = payload.get("history") if isinstance(payload.get("history"), list) else []

    if not history:
        watchlist = {
            "watchlist_id": _watchlist_id(timestamp_utc=ts, items=[]),
            "timestamp_utc": ts,
            "items": [],
            "provenance": {
                "source": "abx.report_manifest_watchlist.build_report_manifest_watchlist",
                "reason": str(payload.get("reason", f"report_missing:{LEDGER_PATH.as_posix()}")),
                "deterministic_ordering": ["watchlist_id", "timestamp_utc", "items", "provenance"],
            },
        }
        jsonschema.Draft202012Validator(_load_schema()).validate(watchlist)
        return {"status": "NOT_COMPUTABLE", "reason": str(payload.get("reason", "history_missing")), "watchlist": watchlist}

    stats: dict[str, dict[str, Any]] = {}
    for row in history:
        if not isinstance(row, dict):
            continue
        ts_row = str(row.get("timestamp_utc", "NOT_COMPUTABLE"))
        events = row.get("artifact_events") if isinstance(row.get("artifact_events"), list) else []
        if not events:
            # Backward compatibility for older ledger rows.
            events = [{
                "artifact_type": "UNKNOWN",
                "hash_changed_count": int(row.get("hash_changed_count", 0) or 0),
                "freshness_changed_count": int(row.get("freshness_changed_count", 0) or 0),
                "status_changed_count": int(row.get("status_changed_count", 0) or 0),
                "removed_count": int(row.get("removed_count", 0) or 0),
            }]

        for event in events:
            artifact = str(event.get("artifact_type", "UNKNOWN"))
            if artifact not in stats:
                stats[artifact] = {
                    "hash": 0,
                    "freshness": 0,
                    "status": 0,
                    "removed": 0,
                    "last_seen_timestamp": "NOT_COMPUTABLE",
                }
            stats[artifact]["hash"] += int(event.get("hash_changed_count", 0) or 0)
            stats[artifact]["freshness"] += int(event.get("freshness_changed_count", 0) or 0)
            stats[artifact]["status"] += int(event.get("status_changed_count", 0) or 0)
            stats[artifact]["removed"] += int(event.get("removed_count", 0) or 0)
            stats[artifact]["last_seen_timestamp"] = ts_row

    items: list[dict[str, Any]] = []
    for artifact in sorted(stats.keys()):
        row = stats[artifact]
        if int(row["hash"]) >= THRESHOLDS["hash"]:
            items.append(
                {
                    "artifact_type": artifact,
                    "issue_type": "REPEATED_HASH_CHURN",
                    "occurrence_count": int(row["hash"]),
                    "last_seen_timestamp": str(row["last_seen_timestamp"]),
                    "description": "Repeated hash change events across recent diff ledger window.",
                }
            )
        if int(row["freshness"]) >= THRESHOLDS["freshness"]:
            items.append(
                {
                    "artifact_type": artifact,
                    "issue_type": "FREQUENT_STALE_TRANSITION",
                    "occurrence_count": int(row["freshness"]),
                    "last_seen_timestamp": str(row["last_seen_timestamp"]),
                    "description": "Frequent freshness transition events across recent diff ledger window.",
                }
            )
        if int(row["removed"]) >= THRESHOLDS["removed"]:
            items.append(
                {
                    "artifact_type": artifact,
                    "issue_type": "REPEATED_DISAPPEARANCE",
                    "occurrence_count": int(row["removed"]),
                    "last_seen_timestamp": str(row["last_seen_timestamp"]),
                    "description": "Repeated artifact disappearance/removal events across recent diff ledger window.",
                }
            )
        if int(row["status"]) >= THRESHOLDS["status"]:
            items.append(
                {
                    "artifact_type": artifact,
                    "issue_type": "UNSTABLE_STATUS",
                    "occurrence_count": int(row["status"]),
                    "last_seen_timestamp": str(row["last_seen_timestamp"]),
                    "description": "Frequent status-change events across recent diff ledger window.",
                }
            )

    items.sort(key=lambda item: (str(item["artifact_type"]), str(item["issue_type"])))
    watchlist = {
        "watchlist_id": _watchlist_id(timestamp_utc=ts, items=items),
        "timestamp_utc": ts,
        "items": items,
        "provenance": {
            "source": "abx.report_manifest_watchlist.build_report_manifest_watchlist",
            "reason": "ok",
            "window_size": bounded,
            "deterministic_ordering": ["watchlist_id", "timestamp_utc", "items", "provenance"],
        },
    }
    jsonschema.Draft202012Validator(_load_schema()).validate(watchlist)
    return {"status": "OK", "reason": "ok", "watchlist": watchlist}


def write_report_manifest_watchlist(payload: dict[str, Any], path: Path = WATCHLIST_PATH) -> None:
    watchlist = payload.get("watchlist") if isinstance(payload.get("watchlist"), dict) else {}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(watchlist, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def read_report_manifest_watchlist(path: Path = WATCHLIST_PATH) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "NOT_COMPUTABLE",
            "reason": f"report_missing:{path.as_posix()}",
            "watchlist": None,
        }
    watchlist = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": "OK",
        "reason": str((watchlist.get("provenance") if isinstance(watchlist, dict) else {}).get("reason", "ok")),
        "watchlist": watchlist,
    }
