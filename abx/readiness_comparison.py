from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

from abx.developer_readiness import read_developer_readiness_payload
from abx.gap_closure_invariance import read_gap_closure_invariance_payload

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "ReadinessComparisonRecord.v1.json"
LEDGER_PATH = ROOT / "out" / "reports" / "readiness_comparison_ledger.jsonl"
LATEST_PATH = ROOT / "out" / "reports" / "readiness_comparison.latest.json"


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_comparison_id(*, timestamp_utc: str, developer_status: str, developer_run_id: str, gap_run_id: str, gap_readiness_state: str, gap_promotion_decision: str) -> str:
    material = "|".join(
        [timestamp_utc, developer_status, developer_run_id, gap_run_id, gap_readiness_state, gap_promotion_decision]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _alignment_state(dev: dict[str, Any], gap: dict[str, Any], missing_reason: str) -> tuple[str, str]:
    if missing_reason:
        return "NOT_COMPUTABLE", missing_reason

    d_status = str(dev["status"]).upper()
    g_status = str(gap["status"]).upper()
    g_readiness = str(gap["readiness_state"]).upper()
    g_decision = str(gap["promotion_decision"]).upper()

    if d_status == "PASS" and g_decision == "HOLD":
        return "DEV_READY_GAP_HOLD", "developer_readiness_pass_gap_promotion_hold"
    if d_status == "PASS" and (g_readiness in {"READY", "PASS"} or g_decision == "PASS"):
        return "ALIGNED", "developer_ready_and_gap_ready_or_pass"
    if d_status == "PARTIAL" and (g_decision == "HOLD" or g_status in {"PARTIAL", "BLOCKED"} or g_readiness in {"PARTIAL", "PROVISIONAL", "BLOCKED"}):
        return "BOTH_PARTIAL", "developer_partial_and_gap_partial_or_hold"
    if d_status == "PARTIAL" and (g_readiness in {"READY", "PASS"} or g_decision == "PASS"):
        return "DEV_PARTIAL_GAP_READY", "developer_partial_gap_ready"
    if d_status == "NOT_COMPUTABLE" or g_status == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE", "missing_required_projection"
    return "UNKNOWN", "no_descriptive_alignment_rule_matched"


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def build_readiness_comparison_record(*, timestamp_utc: str | None = None) -> dict[str, Any]:
    ts = timestamp_utc or _now_utc()
    developer_payload = read_developer_readiness_payload()
    gap_payload = read_gap_closure_invariance_payload()

    dev_projection = developer_payload.get("projection") if isinstance(developer_payload.get("projection"), dict) else {}
    gap_projection = gap_payload.get("projection") if isinstance(gap_payload.get("projection"), dict) else {}

    dev_checks = dev_projection.get("checks") if isinstance(dev_projection.get("checks"), list) else []
    dev_missing = dev_projection.get("missing_surfaces") if isinstance(dev_projection.get("missing_surfaces"), list) else []

    developer_view = {
        "status": str(developer_payload.get("status", "NOT_COMPUTABLE")),
        "run_id": str(dev_projection.get("run_id", "NOT_COMPUTABLE")),
        "checks_total": len(dev_checks),
        "checks_passed": len([row for row in dev_checks if isinstance(row, dict) and str(row.get("status", "")).upper() == "PASS"]),
        "missing_surfaces_count": len(dev_missing),
    }

    gap_counts = gap_projection.get("invariance_counts") if isinstance(gap_projection.get("invariance_counts"), dict) else {}
    gap_unmet = gap_projection.get("unmet_conditions") if isinstance(gap_projection.get("unmet_conditions"), list) else []

    gap_view = {
        "status": str(gap_payload.get("status", "NOT_COMPUTABLE")),
        "run_id": str(gap_projection.get("run_id", "NOT_COMPUTABLE")),
        "readiness_state": str(gap_projection.get("readiness_state", "NOT_COMPUTABLE")),
        "promotion_decision": str(gap_projection.get("promotion_decision", "HOLD")),
        "invariance_total": int(gap_counts.get("total", 0) or 0),
        "invariance_stable": int(gap_counts.get("stable", 0) or 0),
        "unmet_conditions_count": len(gap_unmet),
    }

    missing_reason = ""
    if str(developer_view["status"]).upper() == "NOT_COMPUTABLE":
        missing_reason = f"developer_readiness_not_computable:{developer_payload.get('reason', 'unknown')}"
    elif str(gap_view["status"]).upper() == "NOT_COMPUTABLE":
        missing_reason = f"gap_closure_invariance_not_computable:{gap_payload.get('reason', 'unknown')}"

    alignment_state, alignment_reason = _alignment_state(developer_view, gap_view, missing_reason)

    comparison_id = _build_comparison_id(
        timestamp_utc=ts,
        developer_status=str(developer_view["status"]),
        developer_run_id=str(developer_view["run_id"]),
        gap_run_id=str(gap_view["run_id"]),
        gap_readiness_state=str(gap_view["readiness_state"]),
        gap_promotion_decision=str(gap_view["promotion_decision"]),
    )

    record = {
        "comparison_id": comparison_id,
        "timestamp_utc": ts,
        "developer_readiness": developer_view,
        "gap_closure_invariance": gap_view,
        "alignment": {
            "state": alignment_state,
            "reason": alignment_reason,
        },
        "provenance": {
            "source": "abx.readiness_comparison.build_readiness_comparison_record",
            "developer_reason": str(developer_payload.get("reason", "unknown")),
            "gap_reason": str(gap_payload.get("reason", "unknown")),
            "deterministic_ordering": [
                "comparison_id",
                "timestamp_utc",
                "developer_readiness",
                "gap_closure_invariance",
                "alignment",
                "provenance",
            ],
        },
    }

    jsonschema.Draft202012Validator(_load_schema()).validate(record)
    return record


def append_comparison_ledger(record: dict[str, Any], ledger_path: Path = LEDGER_PATH, latest_path: Path = LATEST_PATH) -> bool:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    comparison_id = str(record.get("comparison_id", ""))

    existing_ids: set[str] = set()
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            existing_ids.add(str(row.get("comparison_id", "")))

    appended = False
    if comparison_id and comparison_id not in existing_ids:
        with ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        appended = True

    latest_path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return appended


def read_latest_comparison(latest_path: Path = LATEST_PATH) -> dict[str, Any]:
    if not latest_path.exists():
        return {
            "status": "NOT_COMPUTABLE",
            "reason": f"report_missing:{latest_path.as_posix()}",
            "comparison": None,
        }
    comparison = json.loads(latest_path.read_text(encoding="utf-8"))
    return {"status": "OK", "reason": "ok", "comparison": comparison}


def read_ledger_tail(*, limit: int = 20, ledger_path: Path = LEDGER_PATH) -> dict[str, Any]:
    bounded = max(1, min(int(limit), 100))
    if not ledger_path.exists():
        return {
            "status": "NOT_COMPUTABLE",
            "reason": f"report_missing:{ledger_path.as_posix()}",
            "records": [],
        }
    rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {
        "status": "OK",
        "reason": "ok",
        "records": rows[-bounded:],
    }
