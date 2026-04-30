#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.pse.calibration_decision import build_calibration_activation_decision


def _prepare_activation_decision_prereq(repo_root: Path) -> None:
    out = repo_root / "out/reports/pse_calibration_activation_decision.latest.json"
    if out.exists():
        return
    readiness = json.loads((repo_root / "out/reports/abx_readiness_gate.latest.json").read_text(encoding="utf-8"))
    preview = {
        "status": "PREVIEW_ONLY",
        "delta": {"improvement": True},
    }
    state = {"runtime_wiring_enabled": False}
    decision = build_calibration_activation_decision(preview, state, readiness)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")


COMMANDS = [
    {"cmd": ["python", "scripts/run_pse_outcome_tracker.py", "--predictions", "fixtures/pse/scoreable_predictions.v1.json", "--outcomes", "fixtures/pse/scoreable_outcomes.v1.json", "--out", "out/reports/pse_outcome_ledger.latest.json"], "required": True},
    {"cmd": ["python", "scripts/run_pse_brier_ledger.py", "--ledger", "out/reports/pse_outcome_ledger.latest.json", "--out", "out/reports/pse_brier_ledger.latest.json"], "required": True},
    {"cmd": ["python", "scripts/run_abx_readiness_gate.py"], "required": True},
    {"cmd": ["python", "scripts/run_pse_calibration_activation_decision.py"], "required": False},
    {"cmd": ["python", "scripts/run_pse_calibration_candidate_cycle.py"], "required": True},
    {"cmd": ["python", "scripts/run_pse_calibration_candidate_proposal.py"], "required": True},
    {"cmd": ["python", "scripts/run_pse_calibration_candidate_approval_gate.py"], "required": True},
    {"cmd": ["python", "scripts/run_pse_calibration_candidate_apply.py"], "required": True},
    {"cmd": ["python", "scripts/run_pse_calibration_candidate_preview.py"], "required": True},
    {"cmd": ["python", "scripts/run_pse_calibration_activation_review.py"], "required": True},
    {"cmd": ["python", "scripts/run_pse_calibration_runtime_wiring.py"], "required": True},
    {"cmd": ["python", "scripts/run_pse_calibration_post_activation_validation.py"], "required": True},
    {"cmd": ["python", "scripts/run_activation_ledger_receipt.py"], "required": True},
]

REQUIRED_ARTIFACTS = [
    "out/reports/abx_readiness_gate.latest.json",
    "out/reports/pse_calibration_candidate_cycle.latest.json",
    "out/reports/pse_calibration_candidate_proposal.latest.json",
    "out/reports/pse_calibration_candidate_approval_gate.latest.json",
    "out/reports/pse_calibration_candidate_application.latest.json",
    "out/state/pse_calibration_candidate_state.latest.json",
    "out/reports/pse_calibration_candidate_preview.latest.json",
    "out/reports/pse_calibration_activation_review.latest.json",
    "out/reports/pse_calibration_runtime_wiring.latest.json",
    "out/state/pse_calibration_runtime_wiring.latest.json",
    "out/reports/pse_calibration_post_activation_validation.latest.json",
]


def run_completion_pass(repo_root: Path) -> dict:
    execution_log: list[dict] = []
    _prepare_activation_decision_prereq(repo_root)

    for entry in COMMANDS:
        result = subprocess.run(entry["cmd"], cwd=repo_root, check=False)
        execution_log.append({"cmd": entry["cmd"], "returncode": result.returncode})
        if entry["required"] and result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, entry["cmd"])

    missing = [path for path in REQUIRED_ARTIFACTS if not (repo_root / path).exists()]
    receipt = json.loads((repo_root / "out/ledger/pse_calibration_activation_receipt.latest.json").read_text(encoding="utf-8"))

    status = "COMPLETION_SEALED" if not missing and receipt.get("status") == "RECEIPT_SEALED" else "COMPLETION_BLOCKED"
    return {
        "status": status,
        "receipt_status": receipt.get("status", "NOT_COMPUTABLE"),
        "promotion_eligible": receipt.get("promotion", {}).get("eligible") is True,
        "missing_artifacts": missing,
        "execution_log": execution_log,
    }


def main() -> None:
    report = run_completion_pass(REPO_ROOT)
    out_path = REPO_ROOT / "out/ledger/pse_calibration_activation_completion.latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path.as_posix())


if __name__ == "__main__":
    sys.exit(main())
