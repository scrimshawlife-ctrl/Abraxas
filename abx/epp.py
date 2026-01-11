from __future__ import annotations

import argparse

# build_epp replaced by evolve.epp.build capability
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


def main() -> int:
    parser = argparse.ArgumentParser(description="Abraxas EPP v0.1 (proposal pack)")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out-dir", default="out/reports")
    parser.add_argument("--inputs-dir", default="out/reports")
    parser.add_argument(
        "--osh-ledger",
        default="out/osh_ledgers/fetch_artifacts.jsonl",
        help="Path to OSH artifacts ledger",
    )
    parser.add_argument("--integrity-snapshot", default=None)
    parser.add_argument("--dap", default=None)
    parser.add_argument(
        "--mwr",
        default=None,
        help="Optional mimetic weather artifact (out/reports/mwr_<run>.json)",
    )
    parser.add_argument(
        "--a2",
        default=None,
        help="Optional AAlmanac/slang terms artifact (out/reports/a2_<run>.json)",
    )
    parser.add_argument(
        "--a2-phase",
        default=None,
        help="Optional A2 temporal profiles artifact (out/reports/a2_phase_<run>.json)",
    )
    parser.add_argument(
        "--audit",
        default=None,
        help=(
            "Optional forecast audit artifact "
            "(out/forecast_ledger/audits.jsonl or out/reports/forecast_audit_<run>.json)"
        ),
    )
    parser.add_argument(
        "--ledger-path",
        default="out/value_ledgers/epp_runs.jsonl",
        help="Path to EPP ledger",
    )
    args = parser.parse_args()

    # Create context for capability invocation
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.epp",
        git_hash="unknown"
    )

    # Build EPP via capability contract
    epp_result = invoke_capability(
        "evolve.epp.build",
        {
            "run_id": args.run_id,
            "out_dir": args.out_dir,
            "inputs_dir": args.inputs_dir,
            "osh_ledger_path": args.osh_ledger,
            "integrity_snapshot_path": args.integrity_snapshot,
            "dap_path": args.dap,
            "mwr_path": args.mwr,
            "a2_path": args.a2,
            "a2_phase_path": args.a2_phase,
            "audit_path": args.audit,
            "ledger_path": args.ledger_path
        },
        ctx=ctx,
        strict_execution=True
    )
    json_path = epp_result["json_path"]
    md_path = epp_result["md_path"]

    print(f"[EPP] wrote {json_path}")
    print(f"[EPP] wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
