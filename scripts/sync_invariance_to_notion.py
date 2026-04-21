from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_DATABASE_ID = "92ed8970ca2a43a8bc761e04c183ccb7"
DEFAULT_NOTION_VERSION = "2022-06-28"


def _sanitize_promotion(value: Any) -> str:
    recommendation = str(value or "HOLD").upper()
    if recommendation == "PROMOTE":
        return "HOLD"
    return recommendation


def _select(value: Any) -> dict[str, Any]:
    return {"select": {"name": str(value or "NOT_COMPUTABLE")}}


def _rich_text(value: Any) -> dict[str, Any]:
    content = str(value or "")
    return {"rich_text": [{"text": {"content": content}}]}


def _title(value: Any) -> dict[str, Any]:
    content = str(value or "ABX Invariance Row")
    return {"title": [{"text": {"content": content}}]}


def map_row_to_notion_properties(row: dict[str, Any]) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "Name": _title(row.get("Name")),
        "Run ID": _rich_text(row.get("Run ID")),
        "Artifact Type": _select(row.get("Artifact Type")),
        "Artifact Path": _rich_text(row.get("Artifact Path")),
        "Artifact Hash": _rich_text(row.get("Artifact Hash")),
        "Execution Mode": _select(row.get("Execution Mode")),
        "Workspace Scope": _select(row.get("Workspace Scope")),
        "Determinism Pair Status": _select(row.get("Determinism Pair Status")),
        "Invariance State": _select(row.get("Invariance State")),
        "Drift Severity": _select(row.get("Drift Severity")),
        "Repair Loop Reopened": {"checkbox": bool(row.get("Repair Loop Reopened", False))},
        "Validator Status": _select(row.get("Validator Status")),
        "Promotion Recommendation": _select(_sanitize_promotion(row.get("Promotion Recommendation"))),
        "Notes": _rich_text(row.get("Notes")),
    }
    execution_date = row.get("Execution Date")
    if execution_date:
        properties["Execution Date"] = {"date": {"start": str(execution_date)}}
    return properties


def _load_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [dict(item) for item in payload]
    rows = payload.get("rows", [])
    return [dict(item) for item in rows]


def _create_page(token: str, notion_version: str, database_id: str, properties: dict[str, Any]) -> dict[str, Any]:
    request_payload = {"parent": {"database_id": database_id}, "properties": properties}
    request = urllib.request.Request(
        "https://api.notion.com/v1/pages",
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": notion_version,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync ABX invariance tracker rows to Notion.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input or Path("out/reports") / f"{args.run_id}.abx_invariance_tracker_rows.json"
    output_path = args.output or Path("out/reports") / f"{args.run_id}.notion_sync_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"ERROR: input report not found: {input_path.as_posix()}")
        return 1

    rows = _load_rows(input_path)
    mapped_payloads = [map_row_to_notion_properties(row) for row in rows]
    database_id = os.getenv("ABX_INVARIANCE_TRACKER_DATABASE_ID", DEFAULT_DATABASE_ID)
    notion_version = os.getenv("NOTION_VERSION", DEFAULT_NOTION_VERSION)

    if args.dry_run:
        report = {
            "schema_version": "abx_notion_sync_report.v0.1",
            "run_id": args.run_id,
            "status": "PASS",
            "mode": "dry_run",
            "database_id": database_id,
            "row_count": len(rows),
            "mapped_payloads": mapped_payloads,
            "synced_page_ids": [],
            "blockers": [],
        }
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0

    token = os.getenv("NOTION_TOKEN")
    if not token:
        report = {
            "schema_version": "abx_notion_sync_report.v0.1",
            "run_id": args.run_id,
            "status": "BLOCKED",
            "mode": "live",
            "database_id": database_id,
            "row_count": len(rows),
            "mapped_payloads": mapped_payloads,
            "synced_page_ids": [],
            "blockers": ["NOTION_TOKEN missing"],
        }
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 2

    synced_page_ids: list[str] = []
    try:
        for properties in mapped_payloads:
            response = _create_page(
                token=token,
                notion_version=notion_version,
                database_id=database_id,
                properties=properties,
            )
            synced_page_ids.append(str(response.get("id", "")))
    except urllib.error.HTTPError as error:
        report = {
            "schema_version": "abx_notion_sync_report.v0.1",
            "run_id": args.run_id,
            "status": "BLOCKED",
            "mode": "live",
            "database_id": database_id,
            "row_count": len(rows),
            "mapped_payloads": mapped_payloads,
            "synced_page_ids": synced_page_ids,
            "blockers": [f"notion_http_error:{error.code}"],
        }
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 2
    except urllib.error.URLError as error:
        report = {
            "schema_version": "abx_notion_sync_report.v0.1",
            "run_id": args.run_id,
            "status": "BLOCKED",
            "mode": "live",
            "database_id": database_id,
            "row_count": len(rows),
            "mapped_payloads": mapped_payloads,
            "synced_page_ids": synced_page_ids,
            "blockers": [f"notion_transport_error:{error.reason}"],
        }
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 2

    report = {
        "schema_version": "abx_notion_sync_report.v0.1",
        "run_id": args.run_id,
        "status": "PASS",
        "mode": "live",
        "database_id": database_id,
        "row_count": len(rows),
        "mapped_payloads": mapped_payloads,
        "synced_page_ids": synced_page_ids,
        "blockers": [],
    }
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
