#!/usr/bin/env python3
"""Execute Wave large-chunk plan steps and emit deterministic evidence report.

Default execution covers six chunks:
- chunk_a: runtime gate canonicalization guardrails
- chunk_b: behavioral guardrail coverage
- chunk_c: repetition proof loop + N-run gate
- chunk_d: TODO closure artifacts (stub scan/taxonomy/sync)
- chunk_e: artifact verification + sync confirmation
- chunk_f: runtime/ERS coverage stabilization checks
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StepResult:
    name: str
    chunk: str
    command: list[str]
    returncode: int

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _utc_now_iso(now_override: str | None = None) -> str:
    if now_override:
        return str(now_override)
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run_step(*, name: str, chunk: str, command: list[str], cwd: Path) -> StepResult:
    completed = subprocess.run(command, cwd=str(cwd), check=False)
    return StepResult(name=name, chunk=chunk, command=command, returncode=int(completed.returncode))


def _chunk_status(step_results: list[StepResult], chunk: str) -> str:
    chunk_steps = [s for s in step_results if s.chunk == chunk]
    if not chunk_steps:
        return "not_run"
    return "PASS" if all(s.ok for s in chunk_steps) else "FAIL"


def build_report(*, started_at: str, finished_at: str, step_results: list[StepResult], config: dict[str, Any]) -> dict[str, Any]:
    overall_status = "PASS" if all(step.ok for step in step_results) else "FAIL"
    return {
        "version": "wave6_large_chunk_report.v0.3",
        "generated_at": finished_at,
        "started_at": started_at,
        "finished_at": finished_at,
        "overall_status": overall_status,
        "chunks": {
            "chunk_a_runtime_gate": {
                "status": _chunk_status(step_results, "chunk_a"),
                "goal": "Canonical runtime gate behavior stays stable",
            },
            "chunk_b_guardrails": {
                "status": _chunk_status(step_results, "chunk_b"),
                "goal": "Behavioral guardrails remain enforced by tests",
            },
            "chunk_c_repetition_proof": {
                "status": _chunk_status(step_results, "chunk_c"),
                "goal": "Nx deterministic test repetition + N-run gate proof",
            },
            "chunk_d_todo_closure": {
                "status": _chunk_status(step_results, "chunk_d"),
                "goal": "Regenerate TODO/stub scan + taxonomy/sync artifacts from repo state",
            },
            "chunk_e_verification": {
                "status": _chunk_status(step_results, "chunk_e"),
                "goal": "Verify sync artifacts and taxonomy/stub metrics remain consistent",
            },
            "chunk_f_runtime_ers_coverage": {
                "status": _chunk_status(step_results, "chunk_f"),
                "goal": "Protect runtime/ERS boundaries with focused regression checks",
            },
        },
        "config": config,
        "steps": [
            {
                "name": s.name,
                "chunk": s.chunk,
                "ok": s.ok,
                "returncode": s.returncode,
                "command": s.command,
            }
            for s in step_results
        ],
        "provenance": {
            "runner": "scripts.run_large_chunk_plan",
            "python": sys.executable,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Wave large-chunk execution plan and write evidence report")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument(
        "--pytest-target",
        default="tests/test_verify_wave6_artifacts.py",
        help="Pytest module for repetition proof",
    )
    parser.add_argument("--pytest-runs", type=int, default=10, help="How many times to run the target pytest module")
    parser.add_argument("--gate-artifacts-dir", default="artifacts_gate", help="Artifacts directory for N-run gate")
    parser.add_argument("--gate-run-id", default="wave6_chunk_c_gate", help="Run ID for N-run gate")
    parser.add_argument("--gate-runs", type=int, default=10, help="N-run gate run count")
    parser.add_argument("--fixed-now", default="", help="Optional fixed ISO timestamp for deterministic report replay")
    parser.add_argument(
        "--report-out",
        default="docs/artifacts/wave6_chunk_execution_report.json",
        help="Output path for execution report",
    )
    parser.add_argument(
        "--runtime-ers-targets",
        nargs="+",
        default=["tests/test_runtime_infrastructure.py", "tests/test_ers_invariance_gate.py"],
        help="Pytest targets used in chunk F runtime/ERS stabilization checks",
    )
    args = parser.parse_args()

    if args.pytest_runs < 1:
        raise SystemExit("--pytest-runs must be >= 1")
    if args.gate_runs < 1:
        raise SystemExit("--gate-runs must be >= 1")

    repo_root = Path(args.repo_root).resolve()
    fixed_now = args.fixed_now.strip() if isinstance(args.fixed_now, str) else ""
    started_at = _utc_now_iso(fixed_now or None)
    step_results: list[StepResult] = []

    # Chunk A — runtime gate canonicalization
    step_results.append(
        _run_step(
            name="runtime_gate_canonical_tests",
            chunk="chunk_a",
            command=[sys.executable, "-m", "pytest", "tests/test_dozen_run_gate_runtime.py"],
            cwd=repo_root,
        )
    )

    # Chunk B — behavioral guardrail coverage
    step_results.append(
        _run_step(
            name="decodo_guardrail_tests",
            chunk="chunk_b",
            command=[sys.executable, "-m", "pytest", "tests/test_online_decodo_flow.py"],
            cwd=repo_root,
        )
    )

    # Chunk C — repetition proof
    for run_no in range(1, args.pytest_runs + 1):
        step_results.append(
            _run_step(
                name=f"pytest_repetition_{run_no}",
                chunk="chunk_c",
                command=[sys.executable, "-m", "pytest", args.pytest_target],
                cwd=repo_root,
            )
        )

    step_results.append(
        _run_step(
            name="n_run_gate",
            chunk="chunk_c",
            command=[
                sys.executable,
                "-m",
                "scripts.n_run_gate_runtime",
                "--artifacts_dir",
                args.gate_artifacts_dir,
                "--run_id",
                args.gate_run_id,
                "--runs",
                str(args.gate_runs),
            ],
            cwd=repo_root,
        )
    )

    # Chunk D — TODO closure + evidence regeneration
    step_results.append(
        _run_step(
            name="scan_todo_markers",
            chunk="chunk_d",
            command=[sys.executable, "scripts/scan_todo_markers.py"],
            cwd=repo_root,
        )
    )
    step_results.append(
        _run_step(
            name="scan_stubs",
            chunk="chunk_d",
            command=[sys.executable, "scripts/scan_stubs.py", "--write"],
            cwd=repo_root,
        )
    )
    step_results.append(
        _run_step(
            name="build_stub_taxonomy",
            chunk="chunk_d",
            command=[sys.executable, "scripts/build_stub_taxonomy_artifact.py"],
            cwd=repo_root,
        )
    )
    step_results.append(
        _run_step(
            name="build_notion_sync",
            chunk="chunk_d",
            command=[sys.executable, "scripts/build_notion_sync_artifact.py"],
            cwd=repo_root,
        )
    )

    # Chunk E — verification + sync consistency
    step_results.append(
        _run_step(
            name="stub_taxonomy_tests",
            chunk="chunk_e",
            command=[sys.executable, "-m", "pytest", "tests/test_stub_taxonomy_artifact.py"],
            cwd=repo_root,
        )
    )
    step_results.append(
        _run_step(
            name="wave6_artifact_consistency_verify",
            chunk="chunk_e",
            command=[sys.executable, "scripts/verify_wave6_artifacts.py"],
            cwd=repo_root,
        )
    )

    # Chunk F — runtime/ERS stabilization coverage
    step_results.append(
        _run_step(
            name="runtime_ers_stabilization_tests",
            chunk="chunk_f",
            command=[sys.executable, "-m", "pytest", *args.runtime_ers_targets],
            cwd=repo_root,
        )
    )

    finished_at = _utc_now_iso(fixed_now or None)
    config = {
        "repo_root": str(repo_root),
        "pytest_target": args.pytest_target,
        "pytest_runs": args.pytest_runs,
        "gate_artifacts_dir": args.gate_artifacts_dir,
        "gate_run_id": args.gate_run_id,
        "gate_runs": args.gate_runs,
        "runtime_ers_targets": list(args.runtime_ers_targets),
        "chunks_executed": ["chunk_a", "chunk_b", "chunk_c", "chunk_d", "chunk_e", "chunk_f"],
    }
    report = build_report(started_at=started_at, finished_at=finished_at, step_results=step_results, config=config)

    out_path = Path(args.report_out)
    if not out_path.is_absolute():
        out_path = repo_root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[WAVE] report={out_path}")
    print(f"[WAVE] overall_status={report['overall_status']}")
    print(f"[WAVE] chunks_executed={len(config['chunks_executed'])}")
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
