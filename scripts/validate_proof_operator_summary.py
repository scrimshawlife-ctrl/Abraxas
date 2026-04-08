#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from abx.proof_operator_summary_contracts import ProofOperatorSummary


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate proof operator summary against typed contract")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    errors: list[str] = []
    parsed: ProofOperatorSummary | None = None

    summary_path = Path(args.summary)
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        parsed = ProofOperatorSummary.from_dict(payload)
    except Exception as exc:  # deterministic capture
        errors.append(str(exc))

    status = "VALID" if not errors else "INVALID"
    result = {
        "timestamp": utc_now(),
        "label": "proof_operator_summary_contract_validation",
        "summaryPath": str(summary_path),
        "status": status,
        "errors": errors,
        "checkedSummaryId": parsed.summary_id if parsed else None,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    if errors:
        print(f"BLOCKED: wrote invalidation artifact to {out_path}")
        return 1

    print(f"PASS: wrote validation artifact to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
