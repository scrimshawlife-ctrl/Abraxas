from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LATEST_PATH = ROOT / "out" / "reports" / "reporting_cycle.latest.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def cycle_id_from_payload(*, timestamp_utc: str, steps: dict[str, str], overall_status: str, missing_artifacts: list[str]) -> str:
    material = {
        "timestamp_utc": timestamp_utc,
        "steps": {k: steps[k] for k in sorted(steps.keys())},
        "overall_status": overall_status,
        "missing_artifacts": sorted(missing_artifacts),
    }
    packed = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(packed.encode("utf-8")).hexdigest()


def normalize_step_status(value: str, *, ok_values: set[str] | None = None) -> str:
    status = str(value or "NOT_COMPUTABLE").upper()
    if ok_values and status in ok_values:
        return "PASS"
    if status in {"PASS", "FAIL", "PARTIAL", "NOT_COMPUTABLE"}:
        return status
    if status in {"BLOCKED", "HOLD", "DRIFT_DETECTED"}:
        return "PARTIAL"
    return "NOT_COMPUTABLE"


def derive_overall_status(*, steps: dict[str, str], missing_artifacts: list[str]) -> str:
    statuses = [steps[key] for key in [
        "developer_readiness_status",
        "invariance_status",
        "comparison_status",
        "advisory_status",
    ]]
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if any(status == "PARTIAL" for status in statuses):
        return "PARTIAL"
    if missing_artifacts or any(status == "NOT_COMPUTABLE" for status in statuses):
        return "NOT_COMPUTABLE"
    if all(status == "PASS" for status in statuses):
        return "PASS"
    return "NOT_COMPUTABLE"


def read_reporting_cycle(path: Path = LATEST_PATH) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "NOT_COMPUTABLE",
            "reason": f"report_missing:{path.as_posix()}",
            "cycle": None,
        }
    cycle = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": "OK",
        "reason": "ok",
        "cycle": cycle,
        "freshness": cycle.get("freshness") if isinstance(cycle, dict) else None,
    }
