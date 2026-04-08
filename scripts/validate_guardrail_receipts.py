#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from abx.guardrail_receipt_contracts import GuardrailReceiptBundle


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a guardrail receipt bundle against typed contracts")
    parser.add_argument("--bundle", required=True, help="Path to guardrail receipt bundle JSON")
    parser.add_argument("--out", required=True, help="Path to write validation artifact JSON")
    args = parser.parse_args()

    errors: list[str] = []
    parsed_bundle: GuardrailReceiptBundle | None = None

    bundle_path = Path(args.bundle)
    try:
        raw_payload = json.loads(bundle_path.read_text(encoding="utf-8"))
        parsed_bundle = GuardrailReceiptBundle.from_dict(raw_payload)
    except Exception as exc:  # deterministic error capture
        errors.append(str(exc))

    status = "VALID" if not errors else "INVALID"
    payload = {
        "timestamp": utc_now(),
        "label": "guardrail_receipt_contract_validation",
        "bundlePath": str(bundle_path),
        "status": status,
        "errors": errors,
        "checkedReceiptBundleId": parsed_bundle.receipt_bundle_id if parsed_bundle else None,
        "checkedReceiptCount": len(parsed_bundle.receipts) if parsed_bundle else 0,
        "checkedCheckCount": len(parsed_bundle.checks) if parsed_bundle else 0,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    if errors:
        print(f"BLOCKED: wrote invalidation artifact to {out_path}")
        return 1

    print(f"PASS: wrote validation artifact to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
