#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_validator_result(
    run_id: str,
    artifact_id: str,
    ledger_record_id: str,
    packet_id: str,
) -> dict:
    return {
        "timestamp": utc_now(),
        "runId": run_id,
        "artifactId": artifact_id,
        "status": "VALIDATOR-VISIBLE",
        "errors": [],
        "warnings": [],
        "correlation": {
            "packetIds": [packet_id],
            "ledgerRecordIds": [ledger_record_id],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal validator stub for Abraxas proof runs")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--ledger-record-id", required=True)
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--out", required=True, help="Path to write validator artifact JSON")
    args = parser.parse_args()

    result = build_validator_result(
        run_id=args.run_id,
        artifact_id=args.artifact_id,
        ledger_record_id=args.ledger_record_id,
        packet_id=args.packet_id,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"PASS: wrote validator artifact to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
