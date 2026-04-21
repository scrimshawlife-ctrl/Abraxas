from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.core.canonical import sha256_hex


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build gap-closure stabilization report.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def _read_gap_ledger_row(run_id: str, path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for row in reversed(rows):
        if row.get("run_id") == run_id:
            return row
    return None


def _derive_readiness(
    *,
    validation_status: str,
    validator_status: str,
    invariance_counts: dict[str, int],
    has_missing_evidence: bool,
    threshold_rows: int,
) -> tuple[str, str, list[str]]:
    unmet_conditions: list[str] = []
    if has_missing_evidence:
        unmet_conditions.append("missing_required_evidence")
        return ("partial", "BLOCK", unmet_conditions)
    if validation_status != "PASS":
        unmet_conditions.append("closure_validation_report_not_pass")
    if validator_status != "PASS":
        unmet_conditions.append("validator_status_not_pass")
    matched_rows = invariance_counts.get("PROVISIONAL", 0) + invariance_counts.get("STABLE", 0)
    if matched_rows < threshold_rows:
        unmet_conditions.append("invariance_threshold_not_met")
    if invariance_counts.get("BLOCKED", 0) > 0:
        unmet_conditions.append("invariance_blocked_rows_present")
    if invariance_counts.get("DRIFT_DETECTED", 0) > 0:
        unmet_conditions.append("invariance_drift_detected_rows_present")
    if invariance_counts.get("REOPEN_REQUIRED", 0) > 0:
        unmet_conditions.append("invariance_reopen_required_rows_present")
    if unmet_conditions:
        return ("partial", "HOLD", unmet_conditions)
    return ("STABLE_CANDIDATE", "HOLD", [])


def main() -> int:
    args = parse_args()
    run_id = args.run_id
    run_dir = Path("artifacts_seal/runs") / run_id
    out_path = args.output or Path("out/reports/gap_closure_stabilization_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    required = {
        "gap_closure_run": run_dir / "gap_closure_run.json",
        "live_run_projection": run_dir / "live_run_projection.json",
        "closure_validation_report": run_dir / "closure_validation_report.json",
        "validator": Path("out/validators") / f"{run_id}.gap_closure.validator.json",
        "invariance_rows": Path("out/reports") / f"{run_id}.abx_invariance_tracker_rows.json",
    }
    missing = [name for name, path in required.items() if not path.exists()]

    evidence: dict[str, Any] = {}
    for name, path in required.items():
        if path.exists():
            evidence[name] = {"path": path.as_posix(), "sha256": _sha256_file(path)}

    validation_status = "NOT_COMPUTABLE"
    invariance_states: set[str] = set()
    invariance_counts: dict[str, int] = {}
    threshold_rows = 3
    if required["closure_validation_report"].exists():
        validation_status = str(_load_json(required["closure_validation_report"]).get("status", "NOT_COMPUTABLE"))
    validator_status = "NOT_COMPUTABLE"
    if required["validator"].exists():
        validator_status = str(_load_json(required["validator"]).get("status", "NOT_COMPUTABLE"))
    if required["invariance_rows"].exists():
        rows = _load_json(required["invariance_rows"]).get("rows", [])
        invariance_states = {str(row.get("Invariance State", "UNCHECKED")) for row in rows}
        for row in rows:
            state = str(row.get("Invariance State", "UNCHECKED"))
            invariance_counts[state] = invariance_counts.get(state, 0) + 1

    gap_ledger_row = _read_gap_ledger_row(run_id, Path("out/ledger/gap_closure_runs.jsonl"))
    readiness_state, promotion_recommendation, unmet_conditions = _derive_readiness(
        validation_status=validation_status,
        validator_status=validator_status,
        invariance_counts=invariance_counts,
        has_missing_evidence=bool(missing),
        threshold_rows=threshold_rows,
    )
    readiness_reason = "all_thresholds_met" if not unmet_conditions else ";".join(unmet_conditions)

    report = {
        "schema_version": "gap_closure_stabilization_report.v0.1",
        "run_id": run_id,
        "status": "PASS" if not missing else "BLOCKED",
        "readiness_state": readiness_state,
        "readiness_reason": readiness_reason,
        "promotion_recommendation": promotion_recommendation,
        "validation_status": validation_status,
        "validator_status": validator_status,
        "invariance_states": sorted(invariance_states),
        "invariance_counts": dict(sorted(invariance_counts.items())),
        "required_thresholds": {
            "min_provisional_or_stable_rows": threshold_rows,
            "required_validator_status": "PASS",
            "required_validation_status": "PASS",
            "disallowed_invariance_states": ["BLOCKED", "DRIFT_DETECTED", "REOPEN_REQUIRED"],
        },
        "unmet_conditions": unmet_conditions,
        "missing_evidence": missing,
        "evidence": evidence,
        "gap_closure_ledger_row": gap_ledger_row if gap_ledger_row is not None else "NOT_COMPUTABLE",
        "authority_boundary": "projection cannot alter canon status",
    }
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
