from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class StepResult:
    name: str
    ok: bool
    cmd: List[str]
    exit_code: int
    stdout: str
    stderr: str
    artifacts: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _run_step(name: str, argv: List[str], timeout_s: int = 900) -> StepResult:
    proc = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    ok = proc.returncode == 0
    return StepResult(
        name=name,
        ok=ok,
        cmd=argv,
        exit_code=int(proc.returncode),
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        artifacts={},
    )


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Abraxas evolve_run v0.1 (DAP→OSH→EPP→EvoGate→Promote→CanonDiff)"
    )
    p.add_argument("--run-id", required=True)

    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--value-ledger", default="out/value_ledgers/evolve_run_runs.jsonl")

    p.add_argument(
        "--run-mwr",
        action="store_true",
        help="Run mimetic weather + A2 extraction before DAP/OSH/EPP",
    )
    p.add_argument(
        "--oracle-paths",
        nargs="+",
        default=None,
        help="Oracle run files (json/jsonl/md). Required if --run-mwr",
    )
    p.add_argument(
        "--mwr-run-id",
        default=None,
        help="Optional override; default is <run_id>_MWR",
    )
    p.add_argument(
        "--a2-registry",
        default="out/a2_registry/terms.jsonl",
        help="A2 registry jsonl path",
    )
    p.add_argument(
        "--a2-append",
        action="store_true",
        help="Append A2 terms into registry after MWR step",
    )
    p.add_argument(
        "--a2-missed",
        action="store_true",
        help="Emit missed/resurrected A2 report after MWR step",
    )

    p.add_argument("--dap-playbook", default="data/acquire/acquisition_playbook_v0_1.yaml")
    p.add_argument("--osh-offline-requests", default=None)

    p.add_argument("--allowlist-map", default="data/osh/allowlist_url_map.json")
    p.add_argument("--vector-map", default="data/vector_maps/source_vector_map_v0_1.yaml")
    p.add_argument("--allowlist", default="data/osh/allowlist_v0_1.yaml")
    p.add_argument("--osh-ledger", default="out/osh_ledgers/fetch_artifacts.jsonl")

    p.add_argument("--smv", default=None)
    p.add_argument("--cre", default=None)

    p.add_argument("--base-policy", default=None)
    p.add_argument("--baseline-metrics", default=None)
    p.add_argument("--replay-cmd", default=None)
    p.add_argument("--thresholds", default=None)
    p.add_argument("--staging-root", default="out/staging")
    p.add_argument("--build-rim", action="store_true")

    p.add_argument("--emit-canon-snapshot", action="store_true")
    p.add_argument("--force-promote", action="store_true")

    p.add_argument("--continue-on-error", action="store_true")
    p.add_argument("--timeout-s", type=int, default=1200)
    args = p.parse_args()

    run_id = args.run_id
    ts = _utc_now_iso()

    steps: List[StepResult] = []
    artifacts: Dict[str, str] = {}

    def fail_or_continue(step: StepResult) -> bool:
        if step.ok:
            return True
        return bool(args.continue_on_error)

    mwr_json = None
    a2_json = None
    a2_phase_json = None
    a2_phase_md = None
    if args.run_mwr:
        if not args.oracle_paths:
            s0 = StepResult(
                name="mwr",
                ok=False,
                cmd=[
                    "python",
                    "-m",
                    "abx.mwr",
                    "--run-id",
                    "<missing>",
                    "--oracle-paths",
                    "<missing>",
                ],
                exit_code=2,
                stdout="",
                stderr="--run-mwr requires --oracle-paths",
                artifacts={},
            )
            steps.append(s0)
            return _finalize(
                run_id, ts, args.out_reports, steps, artifacts, args.value_ledger, ok=False
            )

        mwr_run_id = args.mwr_run_id or f"{run_id}_MWR"
        mwr_json = os.path.join(args.out_reports, f"mwr_{mwr_run_id}.json")
        a2_json = os.path.join(args.out_reports, f"a2_{mwr_run_id}.json")

        mwr_argv = [
            "python",
            "-m",
            "abx.mwr",
            "--run-id",
            mwr_run_id,
            "--oracle-paths",
            *args.oracle_paths,
            "--out-dir",
            args.out_reports,
        ]
        s0 = _run_step("mwr", mwr_argv, timeout_s=args.timeout_s)
        s0 = StepResult(
            **{**s0.to_dict(), "artifacts": {"mwr_json": mwr_json, "a2_json": a2_json}}
        )
        steps.append(s0)
        artifacts["mwr_json"] = mwr_json
        artifacts["a2_json"] = a2_json
        artifacts["mwr_run_id"] = mwr_run_id
        if not fail_or_continue(s0):
            return _finalize(
                run_id, ts, args.out_reports, steps, artifacts, args.value_ledger, ok=False
            )

        if args.a2_append or args.a2_missed:
            reg_argv = [
                "python",
                "-m",
                "abx.a2_registry",
                "--a2",
                a2_json,
                "--registry",
                args.a2_registry,
                "--out-reports",
                args.out_reports,
                "--run-id",
                run_id,
            ]
            if args.a2_append:
                reg_argv.append("--append")
            if args.a2_missed:
                reg_argv.append("--missed-report")
            s0b = _run_step("a2_registry", reg_argv, timeout_s=args.timeout_s)
            steps.append(s0b)
            if args.a2_missed:
                artifacts["a2_missed_json"] = os.path.join(
                    args.out_reports, f"a2_missed_{run_id}.json"
                )
                artifacts["a2_missed_md"] = os.path.join(
                    args.out_reports, f"a2_missed_{run_id}.md"
                )
            if not fail_or_continue(s0b):
                return _finalize(
                    run_id,
                    ts,
                    args.out_reports,
                    steps,
                    artifacts,
                    args.value_ledger,
                    ok=False,
                )

    a2_phase_json = os.path.join(args.out_reports, f"a2_phase_{run_id}.json")
    a2_phase_md = os.path.join(args.out_reports, f"a2_phase_{run_id}.md")
    a2_phase_argv = [
        "python",
        "-m",
        "abx.a2_phase",
        "--run-id",
        run_id,
        "--registry",
        args.a2_registry,
        "--out-reports",
        args.out_reports,
    ]
    s0c = _run_step("a2_phase", a2_phase_argv, timeout_s=args.timeout_s)
    s0c = StepResult(
        **{
            **s0c.to_dict(),
            "artifacts": {"a2_phase_json": a2_phase_json, "a2_phase_md": a2_phase_md},
        }
    )
    steps.append(s0c)
    artifacts["a2_phase_json"] = a2_phase_json
    artifacts["a2_phase_md"] = a2_phase_md
    if not fail_or_continue(s0c):
        return _finalize(
            run_id, ts, args.out_reports, steps, artifacts, args.value_ledger, ok=False
        )

    dap_json = os.path.join(args.out_reports, f"dap_{run_id}.json")
    dap_argv = [
        "python",
        "-m",
        "abx.dap",
        "--run-id",
        run_id,
        "--playbook",
        args.dap_playbook,
    ]
    if args.osh_offline_requests:
        dap_argv += ["--osh-offline-requests", args.osh_offline_requests]
    s1 = _run_step("dap", dap_argv, timeout_s=args.timeout_s)
    s1 = StepResult(**{**s1.to_dict(), "artifacts": {"dap_json": dap_json}})
    steps.append(s1)
    artifacts["dap_json"] = dap_json
    if not fail_or_continue(s1):
        return _finalize(run_id, ts, args.out_reports, steps, artifacts, args.value_ledger, ok=False)

    osh_argv = [
        "python",
        "-m",
        "abx.osh",
        "--run-id",
        run_id,
        "--dap",
        dap_json,
        "--allowlist-map",
        args.allowlist_map,
        "--vector-map",
        args.vector_map,
        "--allowlist",
        args.allowlist,
    ]
    s2 = _run_step("osh", osh_argv, timeout_s=args.timeout_s)
    s2 = StepResult(**{**s2.to_dict(), "artifacts": {"osh_ledger": args.osh_ledger}})
    steps.append(s2)
    artifacts["osh_ledger"] = args.osh_ledger
    if not fail_or_continue(s2):
        return _finalize(run_id, ts, args.out_reports, steps, artifacts, args.value_ledger, ok=False)

    epp_json = os.path.join(args.out_reports, f"epp_{run_id}.json")
    epp_md = os.path.join(args.out_reports, f"epp_{run_id}.md")
    epp_argv = [
        "python",
        "-m",
        "abx.epp",
        "--run-id",
        run_id,
        "--out-dir",
        args.out_reports,
        "--dap",
        dap_json,
        "--osh-ledger",
        args.osh_ledger,
    ]
    if args.smv:
        epp_argv += ["--smv", args.smv]
        artifacts["smv"] = args.smv
    if args.cre:
        epp_argv += ["--cre", args.cre]
        artifacts["cre"] = args.cre
    if mwr_json and a2_json:
        epp_argv += ["--mwr", mwr_json, "--a2", a2_json]
        artifacts["epp_mwr"] = mwr_json
        artifacts["epp_a2"] = a2_json
    if a2_phase_json:
        epp_argv += ["--a2-phase", a2_phase_json]
        artifacts["epp_a2_phase"] = a2_phase_json
    s3 = _run_step("epp", epp_argv, timeout_s=args.timeout_s)
    s3 = StepResult(
        **{**s3.to_dict(), "artifacts": {"epp_json": epp_json, "epp_md": epp_md}}
    )
    steps.append(s3)
    artifacts["epp_json"] = epp_json
    artifacts["epp_md"] = epp_md
    if not fail_or_continue(s3):
        return _finalize(run_id, ts, args.out_reports, steps, artifacts, args.value_ledger, ok=False)

    evog_json = os.path.join(args.out_reports, f"evogate_{run_id}.json")
    evog_md = os.path.join(args.out_reports, f"evogate_{run_id}.md")
    evog_argv = [
        "python",
        "-m",
        "abx.evogate",
        "--run-id",
        run_id,
        "--epp",
        epp_json,
        "--out-reports",
        args.out_reports,
        "--staging-root",
        args.staging_root,
    ]
    if args.base_policy:
        evog_argv += ["--base-policy", args.base_policy]
        artifacts["base_policy"] = args.base_policy
    if args.baseline_metrics:
        evog_argv += ["--baseline-metrics", args.baseline_metrics]
        artifacts["baseline_metrics"] = args.baseline_metrics
    if args.replay_cmd:
        evog_argv += ["--replay-cmd", args.replay_cmd]
    if args.thresholds:
        evog_argv += ["--thresholds", args.thresholds]
    if args.build_rim:
        evog_argv += ["--build-rim-from-osh-ledger", args.osh_ledger]
        artifacts["rim_manifest"] = os.path.join(
            "out", "replay_inputs", run_id, "manifest.json"
        )
    s4 = _run_step("evogate", evog_argv, timeout_s=args.timeout_s)
    s4 = StepResult(
        **{
            **s4.to_dict(),
            "artifacts": {"evogate_json": evog_json, "evogate_md": evog_md},
        }
    )
    steps.append(s4)
    artifacts["evogate_json"] = evog_json
    artifacts["evogate_md"] = evog_md
    if not fail_or_continue(s4):
        return _finalize(run_id, ts, args.out_reports, steps, artifacts, args.value_ledger, ok=False)

    candidate_policy = os.path.join(args.staging_root, run_id, "candidate_policy.json")
    artifacts["candidate_policy"] = candidate_policy

    rim_manifest = artifacts.get("rim_manifest") or os.path.join(
        "out", "replay_inputs", run_id, "manifest.json"
    )
    promote_argv = [
        "python",
        "-m",
        "abx.promote",
        "--run-id",
        run_id,
        "--epp",
        epp_json,
        "--evogate",
        evog_json,
        "--rim",
        rim_manifest,
        "--candidate-policy",
        candidate_policy,
    ]
    if args.emit_canon_snapshot:
        promote_argv += ["--emit-canon-snapshot"]
    if args.force_promote:
        promote_argv += ["--force"]
    s5 = _run_step("promote", promote_argv, timeout_s=args.timeout_s)
    steps.append(s5)
    if not fail_or_continue(s5):
        return _finalize(run_id, ts, args.out_reports, steps, artifacts, args.value_ledger, ok=False)

    canon_diff_json = os.path.join(args.out_reports, f"canon_diff_{run_id}.json")
    canon_diff_md = os.path.join(args.out_reports, f"canon_diff_{run_id}.md")
    canon_diff_argv = [
        "python",
        "-m",
        "abx.canon_diff",
        "--run-id",
        run_id,
        "--candidate-policy",
        candidate_policy,
        "--out-reports",
        args.out_reports,
        "--evogate",
        evog_json,
        "--rim",
        rim_manifest,
        "--epp",
        epp_json,
    ]
    s6 = _run_step("canon_diff", canon_diff_argv, timeout_s=args.timeout_s)
    s6 = StepResult(
        **{
            **s6.to_dict(),
            "artifacts": {
                "canon_diff_json": canon_diff_json,
                "canon_diff_md": canon_diff_md,
            },
        }
    )
    steps.append(s6)
    artifacts["canon_diff_json"] = canon_diff_json
    artifacts["canon_diff_md"] = canon_diff_md
    if not fail_or_continue(s6):
        return _finalize(run_id, ts, args.out_reports, steps, artifacts, args.value_ledger, ok=False)

    bundle_md = os.path.join(args.out_reports, f"run_bundle_{run_id}.md")
    _write_text(bundle_md, _render_bundle_md(run_id, ts, steps, artifacts))
    artifacts["run_bundle_md"] = bundle_md

    return _finalize(run_id, ts, args.out_reports, steps, artifacts, args.value_ledger, ok=True)


def _render_bundle_md(
    run_id: str,
    ts: str,
    steps: List[StepResult],
    artifacts: Dict[str, str],
) -> str:
    lines: List[str] = []
    lines.append("# Evolve Run Bundle v0.1\n")
    lines.append(f"- run_id: `{run_id}`")
    lines.append(f"- ts: `{ts}`\n")

    lines.append("## Artifacts\n")
    for key in sorted(artifacts.keys()):
        lines.append(f"- {key}: `{artifacts[key]}`")
    lines.append("")

    lines.append("## Steps\n")
    for step in steps:
        status = "ok" if step.ok else f"FAIL({step.exit_code})"
        lines.append(f"### {step.name}: {status}")
        lines.append(f"- cmd: `{' '.join(shlex.quote(x) for x in step.cmd)}`")
        if step.artifacts:
            lines.append("- step artifacts:")
            for artifact_key, artifact_value in step.artifacts.items():
                lines.append(f"  - {artifact_key}: `{artifact_value}`")
        if step.stdout:
            tail = "\n".join(step.stdout.splitlines()[-20:])
            lines.append("\n**stdout (tail)**\n```")
            lines.append(tail)
            lines.append("```")
        if step.stderr:
            tail = "\n".join(step.stderr.splitlines()[-20:])
            lines.append("\n**stderr (tail)**\n```")
            lines.append(tail)
            lines.append("```")
        lines.append("")
    return "\n".join(lines) + "\n"


def _finalize(
    run_id: str,
    ts: str,
    out_reports: str,
    steps: List[StepResult],
    artifacts: Dict[str, str],
    ledger_path: str,
    ok: bool,
) -> int:
    record = {
        "run_id": run_id,
        "ts": ts,
        "ok": bool(ok),
        "steps": [
            {"name": step.name, "ok": step.ok, "exit_code": step.exit_code}
            for step in steps
        ],
        "artifacts": dict(artifacts),
    }
    # Use capability contract for ledger append
    ctx = RuneInvocationContext(run_id=run_id, subsystem_id="abx.evolve_run", git_hash="unknown")
    invoke_capability("evolve.ledger.append", {"path": ledger_path, "record": record}, ctx=ctx, strict_execution=True)
    summary_path = os.path.join(out_reports, f"run_bundle_{run_id}.json")
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2, sort_keys=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
