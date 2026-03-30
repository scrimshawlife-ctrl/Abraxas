#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.promotion_policy import (
    PromotionPolicyDecision,
    PromotionPolicyState,
    emit_promotion_policy,
    evaluate_promotion_policy,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


@dataclass(frozen=True)
class StepResult:
    name: str
    command: list[str]
    returncode: int
    ok: bool


def policy_allows_tier3_execution(decision_state: str | None) -> bool:
    return decision_state in {PromotionPolicyState.ALLOWED.value, PromotionPolicyState.WAIVED.value}


def compute_overall_status(
    *,
    validator_status: str | None,
    acceptance_verdict: str | None,
    seal_ok: bool | None,
    require_seal: bool,
    policy_decision_state: str | None,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not policy_allows_tier3_execution(policy_decision_state):
        reasons.append(f"policy_decision_state={policy_decision_state or 'missing'}")
    if validator_status != "VALID":
        reasons.append(f"validator_status={validator_status or 'missing'}")
    if acceptance_verdict != "PASS":
        reasons.append(f"acceptance_verdict={acceptance_verdict or 'missing'}")
    if require_seal and seal_ok is not True:
        reasons.append(f"seal_ok={seal_ok}")
    return ("PASS", []) if not reasons else ("FAIL", reasons)


def _run_step(name: str, command: list[str], cwd: Path) -> StepResult:
    completed = subprocess.run(command, cwd=str(cwd), check=False)
    return StepResult(
        name=name,
        command=command,
        returncode=int(completed.returncode),
        ok=(completed.returncode == 0),
    )


def build_attestation_payload(
    *,
    run_id: str,
    started_at: str,
    finished_at: str,
    step_results: list[StepResult],
    validator_artifact: Path,
    acceptance_result: Path,
    acceptance_status: Path,
    seal_report: Path | None,
    require_seal: bool,
    policy_decision: PromotionPolicyDecision,
    policy_artifact: Path,
) -> dict[str, Any]:
    validator_payload = _safe_read_json(validator_artifact)
    acceptance_payload = _safe_read_json(acceptance_result)
    seal_payload = _safe_read_json(seal_report) if seal_report else None

    validator_status = None
    if validator_payload and isinstance(validator_payload.get("status"), str):
        validator_status = str(validator_payload["status"])

    acceptance_verdict = None
    if acceptance_payload and isinstance(acceptance_payload.get("overall_verdict"), str):
        acceptance_verdict = str(acceptance_payload["overall_verdict"])

    seal_ok = None
    if isinstance(seal_payload, dict):
        seal_ok = bool(seal_payload.get("ok"))

    overall_status, reasons = compute_overall_status(
        validator_status=validator_status,
        acceptance_verdict=acceptance_verdict,
        seal_ok=seal_ok,
        require_seal=require_seal,
        policy_decision_state=policy_decision.decision_state.value,
    )

    return {
        "schema": "ExecutionAttestation.v1",
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "overall_status": overall_status,
        "fail_reasons": reasons,
        "steps": [
            {
                "name": step.name,
                "ok": step.ok,
                "returncode": step.returncode,
                "command": step.command,
            }
            for step in step_results
        ],
        "artifacts": {
            "policy": {
                "path": policy_artifact.as_posix(),
                "exists": policy_artifact.exists(),
            },
            "validator": {
                "path": validator_artifact.as_posix(),
                "exists": validator_artifact.exists(),
                "status": validator_status,
            },
            "acceptance_result": {
                "path": acceptance_result.as_posix(),
                "exists": acceptance_result.exists(),
                "overall_verdict": acceptance_verdict,
            },
            "acceptance_status": {
                "path": acceptance_status.as_posix(),
                "exists": acceptance_status.exists(),
            },
            "seal_report": {
                "path": seal_report.as_posix() if seal_report else "",
                "exists": bool(seal_report and seal_report.exists()),
                "ok": seal_ok,
                "required": require_seal,
            },
        },
        "policy_gate": {
            "decision_state": policy_decision.decision_state.value,
            "reason_codes": policy_decision.reason_codes[:8],
            "blockers": policy_decision.blockers[:8],
            "waived": policy_decision.waived,
            "requires_federation": policy_decision.requires_federation,
            "federated_evidence": policy_decision.federated_evidence_summary,
        },
        "provenance": {
            "runner": "scripts.run_execution_attestation",
            "version": "v0.3",
            "policy_checker": policy_decision.provenance.get("checker", "unknown"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified execution attestation runner")
    parser.add_argument("run_id", help="Run identifier for execution validator")
    parser.add_argument("--base-dir", default=".", help="Repository base path")
    parser.add_argument("--validators-out", default="out/validators", help="Validator output directory")
    parser.add_argument("--acceptance-output", default="out/acceptance", help="Acceptance output directory")
    parser.add_argument(
        "--acceptance-input",
        default="tests/fixtures/acceptance/baseline_input.json",
        help="Acceptance suite baseline input JSON",
    )
    parser.add_argument("--acceptance-runs", type=int, default=12, help="Acceptance determinism run count")
    parser.add_argument("--with-seal", action="store_true", help="Include seal release step")
    parser.add_argument("--seal-run-id", default="seal", help="Seal run id (used when --with-seal enabled)")
    parser.add_argument("--attestation-out", default="out/attestation", help="Attestation output directory")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    started_at = _utc_now_iso()
    steps: list[StepResult] = []

    policy_decision = evaluate_promotion_policy(args.run_id, base_dir=base_dir)
    policy_artifact = emit_promotion_policy(policy_decision, base_dir / "out" / "policy")

    validator_artifact = base_dir / args.validators_out / f"execution-validation-{args.run_id}.json"
    acceptance_result = base_dir / args.acceptance_output / "acceptance_result.json"
    acceptance_status = base_dir / args.acceptance_output / "acceptance_status_v1.json"
    seal_report: Path | None = None

    if not policy_allows_tier3_execution(policy_decision.decision_state.value):
        finished_at = _utc_now_iso()
        payload = build_attestation_payload(
            run_id=args.run_id,
            started_at=started_at,
            finished_at=finished_at,
            step_results=steps,
            validator_artifact=validator_artifact,
            acceptance_result=acceptance_result,
            acceptance_status=acceptance_status,
            seal_report=seal_report,
            require_seal=args.with_seal,
            policy_decision=policy_decision,
            policy_artifact=policy_artifact,
        )

        out_dir = base_dir / args.attestation_out
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"execution-attestation-{args.run_id}.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        print(f"attestation={out_path}")
        print(f"overall_status={payload['overall_status']}")
        if payload["fail_reasons"]:
            print("fail_reasons=" + ",".join(payload["fail_reasons"]))
        return 1

    validator_cmd = [
        sys.executable,
        "scripts/run_execution_validator.py",
        args.run_id,
        "--base-dir",
        str(base_dir),
        "--out-dir",
        args.validators_out,
    ]
    steps.append(_run_step("execution_validator", validator_cmd, base_dir))

    acceptance_cmd = [
        sys.executable,
        "tools/acceptance/run_acceptance_suite.py",
        "--input",
        args.acceptance_input,
        "--runs",
        str(args.acceptance_runs),
        "--output",
        args.acceptance_output,
    ]
    steps.append(_run_step("acceptance_suite", acceptance_cmd, base_dir))

    if args.with_seal:
        seal_cmd = [
            sys.executable,
            "-m",
            "scripts.seal_release",
            "--run_id",
            args.seal_run_id,
        ]
        steps.append(_run_step("seal_release", seal_cmd, base_dir))
        seal_report = base_dir / "artifacts_seal" / "runs" / f"{args.seal_run_id}.sealreport.json"

    finished_at = _utc_now_iso()

    payload = build_attestation_payload(
        run_id=args.run_id,
        started_at=started_at,
        finished_at=finished_at,
        step_results=steps,
        validator_artifact=validator_artifact,
        acceptance_result=acceptance_result,
        acceptance_status=acceptance_status,
        seal_report=seal_report,
        require_seal=args.with_seal,
        policy_decision=policy_decision,
        policy_artifact=policy_artifact,
    )

    out_dir = base_dir / args.attestation_out
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"execution-attestation-{args.run_id}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"attestation={out_path}")
    print(f"overall_status={payload['overall_status']}")
    if payload["fail_reasons"]:
        print("fail_reasons=" + ",".join(payload["fail_reasons"]))
    return 0 if payload["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
