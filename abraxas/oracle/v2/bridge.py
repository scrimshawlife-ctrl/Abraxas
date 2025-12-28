from __future__ import annotations

import argparse
import os
import shlex
import subprocess
from typing import List, Optional

from abraxas.oracle.v2.cli import main as v2_main


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
    p.add_argument("--config-hash", required=True, help="Deterministic config hash for v2 provenance")
    p.add_argument("--v1-cmd", required=True, help="Command to run the existing v1 oracle (quoted string)")
    p.add_argument("--v1-out-dir", default="out", help="Where v1 writes out/latest/envelope.json (default: out)")
    p.add_argument("--out-dir", default="out", help="Where v2 writes outputs (default: out)")
    p.add_argument("--mode", default="", choices=["", "SNAPSHOT", "ANALYST", "RITUAL"], help="Optional user mode request")
    p.add_argument("--bw-high", type=float, default=20.0, help="Router BW_HIGH threshold (default: 20)")
    p.add_argument("--mrs-high", type=float, default=70.0, help="Router MRS_HIGH threshold (default: 70)")
    p.add_argument("--no-ledger", action="store_true", help="Disable stabilization ledger tick")
    p.add_argument("--ledger-path", default="", help="Override stabilization ledger path (optional)")
    args = p.parse_args(argv)

    # 1) Run v1
    v1_cmd = shlex.split(args.v1_cmd)
    rc1 = _run_cmd(v1_cmd)
    if rc1 != 0:
        return rc1

    # 2) Run v2 shim (auto-discover v1 envelope)
    v2_args: List[str] = [
        "--config-hash", args.config_hash,
        "--auto-in-envelope",
        "--v1-out-dir", args.v1_out_dir,
        "--out-dir", args.out_dir,
        "--bw-high", str(args.bw_high),
        "--mrs-high", str(args.mrs_high),
    ]
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
