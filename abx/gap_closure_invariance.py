from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = ROOT / "out" / "reports" / "gap_closure_stabilization_report.json"
PROJECTION_SCHEMA_PATH = ROOT / "schemas" / "GapClosureInvarianceProjection.v1.json"


def _sorted_object(value: dict[str, Any]) -> dict[str, Any]:
    return {key: value[key] for key in sorted(value.keys())}


def _normalize_counts(raw_counts: dict[str, Any]) -> dict[str, int]:
    checked = {
        "unchecked": int(raw_counts.get("UNCHECKED", 0) or 0),
        "provisional": int(raw_counts.get("PROVISIONAL", 0) or 0),
        "stable": int(raw_counts.get("STABLE", 0) or 0),
    }
    checked["total"] = checked["unchecked"] + checked["provisional"] + checked["stable"]
    return {
        "total": checked["total"],
        "unchecked": checked["unchecked"],
        "provisional": checked["provisional"],
        "stable": checked["stable"],
    }


def project_gap_closure_invariance(raw: dict[str, Any], source_path: Path = DEFAULT_REPORT_PATH) -> dict[str, Any]:
    raw_counts = raw.get("invariance_counts") if isinstance(raw.get("invariance_counts"), dict) else {}
    required_thresholds = raw.get("required_thresholds") if isinstance(raw.get("required_thresholds"), dict) else {}
    unmet_conditions = sorted(str(item) for item in raw.get("unmet_conditions", []) if str(item))
    run_id = str(raw.get("run_id", "NOT_COMPUTABLE"))

    input_hash = hashlib.sha256(
        json.dumps(
            {
                "run_id": run_id,
                "invariance_counts": raw_counts,
                "required_thresholds": required_thresholds,
                "unmet_conditions": unmet_conditions,
                "readiness_state": raw.get("readiness_state", "NOT_COMPUTABLE"),
                "promotion_recommendation": raw.get("promotion_recommendation", raw.get("promotion_decision", "HOLD")),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    projection = {
        "run_id": run_id,
        "invariance_counts": _normalize_counts(raw_counts),
        "required_thresholds": _sorted_object(dict(required_thresholds)),
        "unmet_conditions": unmet_conditions,
        "readiness_state": str(raw.get("readiness_state", "NOT_COMPUTABLE")),
        "promotion_decision": str(raw.get("promotion_recommendation", raw.get("promotion_decision", "HOLD"))),
        "provenance": {
            "source": "abx.gap_closure_invariance.project_gap_closure_invariance",
            "source_path": source_path.as_posix(),
            "input_hash": input_hash,
            "projection_generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "deterministic_ordering": [
                "run_id",
                "invariance_counts.total",
                "invariance_counts.unchecked",
                "invariance_counts.provisional",
                "invariance_counts.stable",
                "required_thresholds",
                "unmet_conditions",
                "readiness_state",
                "promotion_decision",
            ],
        },
    }

    with PROJECTION_SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    jsonschema.Draft202012Validator(schema).validate(projection)
    return projection


def read_gap_closure_invariance_payload(report_path: Path = DEFAULT_REPORT_PATH) -> dict[str, Any]:
    if not report_path.exists():
        projection = {
            "run_id": "NOT_COMPUTABLE",
            "invariance_counts": {"total": 0, "unchecked": 0, "provisional": 0, "stable": 0},
            "required_thresholds": {},
            "unmet_conditions": ["missing_gap_closure_stabilization_report"],
            "readiness_state": "NOT_COMPUTABLE",
            "promotion_decision": "HOLD",
            "provenance": {
                "source": "abx.gap_closure_invariance.read_gap_closure_invariance_payload",
                "source_path": report_path.as_posix(),
                "input_hash": "NOT_COMPUTABLE",
                "projection_generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "deterministic_ordering": [],
            },
        }
        return {
            "status": "NOT_COMPUTABLE",
            "reason": f"report_missing:{report_path.as_posix()}",
            "raw": None,
            "projection": projection,
        }

    raw = json.loads(report_path.read_text(encoding="utf-8"))
    projection = project_gap_closure_invariance(raw, source_path=report_path)
    return {
        "status": str(raw.get("status", "NOT_COMPUTABLE")),
        "reason": "ok",
        "raw": raw,
        "projection": projection,
    }
