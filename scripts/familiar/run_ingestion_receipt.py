#!/usr/bin/env python3
"""Mint a SHADOW FamiliarIngestionReceipt.v0 from a local EvidencePack JSON.

Usage:
  python scripts/familiar/run_ingestion_receipt.py --pack PATH
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx_familiar.ingest.familiar_ingestion_receipt import (
    build_familiar_ingestion_receipt_from_path,
    write_familiar_ingestion_receipt,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args(argv)

    receipt = build_familiar_ingestion_receipt_from_path(args.pack)
    if args.print_only:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        if args.out is not None:
            out_path = args.out
        else:
            stem = Path(args.pack).stem.replace(".v0", "")
            out_path = ROOT / "out" / "ingest" / "familiar_ingestion" / f"{stem}_receipt.v0.json"
        write_familiar_ingestion_receipt(out_path, receipt)
        print(
            json.dumps(
                {
                    "wrote": str(out_path),
                    "status": receipt["status"],
                    "receipt_id": receipt["receipt_id"],
                    "receipt_hash": receipt["receipt_hash"],
                },
                indent=2,
            )
        )
    return 0 if receipt.get("status") == "INGESTED_SHADOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
