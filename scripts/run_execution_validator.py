#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.execution_validator import emit_validation_result, validate_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Run execution validator for a specific run id")
    parser.add_argument("run_id", help="Run identifier to validate")
    parser.add_argument("--base-dir", default=".", help="Repository base path")
    parser.add_argument("--out-dir", default="out/validators", help="Directory for validator artifact json")
    args = parser.parse_args()

    result = validate_run(args.run_id, base_dir=Path(args.base_dir))
    out_path = emit_validation_result(result, Path(args.out_dir))

    print(f"run_id={result.run_id}")
    print(f"status={result.status.value}")
    print(f"valid={result.valid}")
    print(f"ledger_records={len(result.ledger_record_ids)}")
    print(f"artifacts={len(result.ledger_artifact_ids)}")
    print(f"output={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
