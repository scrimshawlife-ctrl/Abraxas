from __future__ import annotations

import argparse
import os
import shlex
import subprocess
from typing import List, Optional

from abraxas.oracle.v2.cli import main as v2_main
from abraxas.oracle.v2.config import load_or_create_config


def _run_cmd(cmd: List[str]) -> int:
    """
    Deterministic execution wrapper:
      - no shell=True
      - inherits stdout/stderr so CI logs are visible
    """
    p = subprocess.run(cmd, check=False)
    return int(p.returncode)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="abraxas.oracle.bridge")
    p.add_argument("--config-hash", default="", help="Deterministic config hash for v2 provenance (optional if --config used)")
    p.add_argument("--config", default="", help="Path to v2 config json (auto-created if missing when provided)")
    p.add_argument("--profile", default="default", help="Config profile (default: default)")
    p.add_argument("--schema-index", default="", help="Schema index path (default: schema/v2/index.json)")
    p.add_argument("--v1-cmd", required=True, help="Command to run the existing v1 oracle (quoted string)")
    p.add_argument("--v1-out-dir", default="out", help="Where v1 writes out/latest/envelope.json (default: out)")
    p.add_argument("--out-dir", default="out", help="Where v2 writes outputs (default: out)")
    p.add_argument("--mode", default="", choices=["", "SNAPSHOT", "ANALYST", "RITUAL"], help="Optional user mode request")
    p.add_argument("--bw-high", type=float, default=20.0, help="Router BW_HIGH threshold (default: 20)")
    p.add_argument("--mrs-high", type=float, default=70.0, help="Router MRS_HIGH threshold (default: 70)")
    p.add_argument("--no-ledger", action="store_true", help="Disable stabilization ledger tick")
    p.add_argument("--validate", action="store_true", help="Enable v2 schema validation (default)")
    p.add_argument("--no-validate", action="store_true", help="Disable v2 schema validation")
    p.add_argument("--ledger-path", default="", help="Override stabilization ledger path (optional)")
    args = p.parse_args(argv)

    cfg_hash = args.config_hash
    if not cfg_hash:
        if args.config:
            _, h = load_or_create_config(
                path=args.config,
                profile=args.profile,
                bw_high=float(args.bw_high),
                mrs_high=float(args.mrs_high),
                ledger_enabled=(not args.no_ledger),
                schema_index_path=(args.schema_index if args.schema_index else None) or "schema/v2/index.json",
            )
            cfg_hash = h
        else:
            raise SystemExit("--config-hash is required unless --config is provided")

    # 1) Run v1
    v1_cmd = shlex.split(args.v1_cmd)
    rc1 = _run_cmd(v1_cmd)
    if rc1 != 0:
        return rc1

    # 2) Run v2 shim (auto-discover v1 envelope)
    v2_args: List[str] = [
        "--config-hash", cfg_hash,
        "--auto-in-envelope",
        "--v1-out-dir", args.v1_out_dir,
        "--out-dir", args.out_dir,
        "--bw-high", str(args.bw_high),
        "--mrs-high", str(args.mrs_high),
    ]
    # default validate unless explicitly disabled
    if args.no_validate:
        v2_args.append("--no-validate")

    if args.mode:
        v2_args.extend(["--mode", args.mode])
    if args.no_ledger:
        v2_args.append("--no-ledger")
    if args.ledger_path:
        v2_args.extend(["--ledger-path", args.ledger_path])

    rc2 = v2_main(v2_args)
    return int(rc2)


if __name__ == "__main__":
    raise SystemExit(main())
