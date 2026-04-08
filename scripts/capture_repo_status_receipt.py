#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture structured repo-status receipt")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    cmd = [sys.executable, str(ROOT / ".abraxas" / "scripts" / "repo_status.py")]
    result = subprocess.run(cmd, capture_output=True, text=True)

    parsed = None
    try:
        parsed = json.loads(result.stdout) if result.stdout.strip() else None
    except json.JSONDecodeError:
        parsed = None

    payload = {
        "timestamp": utc_now(),
        "label": "repo_status",
        "command": cmd,
        "returncode": result.returncode,
        "status": "PASS" if result.returncode == 0 else "ATTENTION",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "parsed": parsed,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"PASS: wrote repo-status receipt to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
