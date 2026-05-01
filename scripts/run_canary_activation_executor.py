#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.canary.execution_runner import run_activation_executor
from abraxas.core.canonical import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--activation-packet-run", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--sandbox-root")
    args = parser.parse_args()

    activation_packet_run = json.loads(Path(args.activation_packet_run).read_text(encoding="utf-8"))
    report = run_activation_executor(
        activation_packet_run,
        created_at=args.created_at,
        scope_id=args.scope_id,
        sandbox_root=args.sandbox_root,
    )

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(canonical_json(report) + "\n", encoding="utf-8")
    print(out_path.as_posix())


if __name__ == "__main__":
    main()
