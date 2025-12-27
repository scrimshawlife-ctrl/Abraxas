from __future__ import annotations

import argparse
import os
import subprocess
from datetime import datetime, timezone
from typing import List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run(cmd: List[str]) -> None:
    print("[DAILY_RUN]", " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> int:
    p = argparse.ArgumentParser(description="Abraxas canonical daily run (deterministic)")
    p.add_argument("--run-id", required=True)
    p.add_argument("--oracle-paths", nargs="+", required=True)
    p.add_argument("--out", default="out/reports")
    p.add_argument("--osh-ledger", default="out/osh_ledgers/fetch_artifacts.jsonl")
    p.add_argument("--a2-registry", default="out/a2_registry/terms.jsonl")
    p.add_argument("--predictions", required=True)
    p.add_argument("--emit-proof-bundle", action="store_true")
    p.add_argument("--bundle-root", default="out/proof_bundles")
    args = p.parse_args()

    ts = _utc_now_iso()
    run_id = args.run_id

    os.makedirs(args.out, exist_ok=True)

    _run(
        [
            "python",
            "-m",
            "abx.mwr",
            "--run-id",
            run_id,
            "--oracle-paths",
            *args.oracle_paths,
            "--out-dir",
            args.out,
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.claims_run",
            "--run-id",
            run_id,
            "--osh-ledger",
            args.osh_ledger,
            "--out-reports",
            args.out,
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.a2_registry",
            "--a2",
            os.path.join(args.out, f"a2_{run_id}.json"),
            "--registry",
            args.a2_registry,
            "--out-reports",
            args.out,
            "--run-id",
            run_id,
            "--append",
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.a2_registry",
            "--a2",
            os.path.join(args.out, f"a2_{run_id}.json"),
            "--registry",
            args.a2_registry,
            "--out-reports",
            args.out,
            "--run-id",
            run_id,
            "--missed-report",
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.a2_phase",
            "--run-id",
            run_id,
            "--registry",
            args.a2_registry,
            "--out-reports",
            args.out,
            "--mwr",
            os.path.join(args.out, f"mwr_{run_id}.json"),
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.mwr_enrich",
            "--run-id",
            run_id,
            "--out-reports",
            args.out,
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.term_claims_run",
            "--run-id",
            run_id,
            "--osh-ledger",
            args.osh_ledger,
            "--out-reports",
            args.out,
            "--a2-phase",
            os.path.join(args.out, f"a2_phase_{run_id}.json"),
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.acquisition_plan",
            "--run-id",
            run_id,
            "--out-reports",
            args.out,
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.evidence_tasks",
            "--run-id",
            run_id,
            "--out-reports",
            args.out,
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.evidence_index",
            "--run-id",
            run_id,
            "--bundles-dir",
            "out/evidence_bundles",
            "--out-reports",
            args.out,
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.forecast_score",
            "--run-id",
            run_id,
            "--predictions",
            args.predictions,
            "--a2-phase",
            os.path.join(args.out, f"a2_phase_{run_id}.json"),
            "--mwr",
            os.path.join(args.out, f"mwr_{run_id}.json"),
            "--out-reports",
            args.out,
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.forecast_log",
            "--run-id",
            run_id,
            "--forecast-score",
            os.path.join(args.out, f"forecast_score_{run_id}.json"),
            "--mwr",
            os.path.join(args.out, f"mwr_{run_id}.json"),
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.epp",
            "--run-id",
            run_id,
            "--out-dir",
            args.out,
            "--mwr",
            os.path.join(args.out, f"mwr_{run_id}.json"),
            "--a2-phase",
            os.path.join(args.out, f"a2_phase_{run_id}.json"),
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.horizon_audit",
            "--run-id",
            run_id,
            "--pred-ledger",
            "out/forecast_ledger/predictions.jsonl",
            "--out-ledger",
            "out/forecast_ledger/outcomes.jsonl",
            "--out-reports",
            args.out,
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.horizon_policy_select",
            "--run-id",
            run_id,
            "--pred-ledger",
            "out/forecast_ledger/predictions.jsonl",
            "--out-ledger",
            "out/forecast_ledger/outcomes.jsonl",
            "--out-reports",
            args.out,
        ]
    )

    _run(
        [
            "python",
            "-m",
            "abx.horizon_policy_select_tc",
            "--run-id",
            run_id,
            "--pred-ledger",
            "out/forecast_ledger/predictions.jsonl",
            "--out-ledger",
            "out/forecast_ledger/outcomes.jsonl",
            "--out-reports",
            args.out,
            "--a2-phase",
            os.path.join(args.out, f"a2_phase_{run_id}.json"),
        ]
    )

    if args.emit_proof_bundle:
        _run(
            [
                "python",
                "-m",
                "abx.proof_bundle",
                "--run-id",
                run_id,
                "--out-reports",
                args.out,
                "--bundle-root",
                args.bundle_root,
            ]
        )

    print("[DAILY_RUN] complete:", run_id, ts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
