#!/usr/bin/env python3
"""Run spec v1.1 prefix from a local EvidencePack JSON.

  python scripts/familiar/run_v11_prefix.py --pack PATH
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx_familiar.ingest.pack_io import load_evidence_pack
from abx_familiar.runtime.v11_prefix import run_v11_prefix


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--run-id", default="v11_prefix")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    pack = load_evidence_pack(args.pack)
    # Keep pack_ref as the given path so hashes do not bake a machine absolute.
    result = run_v11_prefix(pack, pack_ref=str(args.pack), run_id=args.run_id)
    if args.out is not None:
        out_path = args.out
    else:
        stem = args.pack.stem.replace(".v0", "")
        out_path = ROOT / "out" / "ingest" / "familiar_v11" / f"{stem}_{args.run_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "wrote": str(out_path),
        "binding_status": result["binding"]["status"],
        "output_hash": result["ledger_entry"].get("output_hash"),
        "output_hash_method": result["ledger_entry"].get("meta", {}).get("output_hash_method"),
        "herald_id": result["herald"].get("delivery_id"),
    }
    print(json.dumps(summary, indent=2))
    return 0 if result["binding"]["status"] == "BOUND_SHADOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
