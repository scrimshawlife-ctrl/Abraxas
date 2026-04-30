#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.pse.brier_ledger import build_brier_ledger
from abraxas.pse.outcome_tracker import build_outcome_ledger

PREDICTIONS_PATH = REPO_ROOT / "fixtures/pse/scoreable_predictions.v1.json"
OUTCOMES_PATH = REPO_ROOT / "fixtures/pse/scoreable_outcomes.v1.json"
OUT_PATH = REPO_ROOT / "out/reports/pse_e2e_fixture_validation.latest.json"


def run_validation() -> dict:
    predictions = json.loads(PREDICTIONS_PATH.read_text(encoding="utf-8"))
    outcomes = json.loads(OUTCOMES_PATH.read_text(encoding="utf-8"))

    outcome_ledger = build_outcome_ledger(predictions, outcomes)
    brier_report = build_brier_ledger(outcome_ledger)

    mean_brier = brier_report["summary"]["mean_brier"]
    assertions = [
        {"id": "scored_count_positive", "status": "PASS" if brier_report["summary"]["scored_count"] > 0 else "FAIL"},
        {"id": "mean_brier_non_null", "status": "PASS" if mean_brier is not None else "FAIL"},
        {"id": "expected_mean_brier", "status": "PASS" if mean_brier == 0.1975 else "FAIL"},
        {"id": "skipped_count_positive", "status": "PASS" if brier_report["summary"]["skipped_count"] > 0 else "FAIL"},
        {"id": "outcome_status_candidate_only", "status": "PASS" if outcome_ledger["status"] == "CANDIDATE_ONLY" else "FAIL"},
        {"id": "brier_status_candidate_only", "status": "PASS" if brier_report["status"] == "CANDIDATE_ONLY" else "FAIL"},
    ]
    status = "PASS" if all(item["status"] == "PASS" for item in assertions) else "FAIL"

    return {
        "schema_version": "PSEE2EValidationReport.v1",
        "status": status,
        "authority": "VALIDATION_ONLY",
        "brier_summary": brier_report["summary"],
        "assertions": assertions,
    }


def main() -> None:
    report = run_validation()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUT_PATH.as_posix())


if __name__ == "__main__":
    main()
