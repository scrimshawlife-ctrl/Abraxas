from __future__ import annotations

import argparse
import json
from pathlib import Path

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.oracle.proof.receipt_writer import write_receipt_artifacts
from abraxas.oracle.proof.validator_summary import build_validator_summary_v2
from abraxas.oracle.runtime.input_normalizer import normalize_input_v2
from abraxas.oracle.runtime.service import run_oracle_signal_layer_v2_service
from abraxas.oracle.stability.digests import compute_digest_triplet
from abraxas.oracle.stability.invariance import run_invariance_v2


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Oracle Signal Layer v2 vertical slice")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-dir", default="out/oracle_signal_layer_v2")
    parser.add_argument("--repeats", type=int, default=12)
    args = parser.parse_args()

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output = run_oracle_signal_layer_v2_service(raw)
    normalized = normalize_input_v2(raw)
    hashes = compute_digest_triplet(normalized=normalized, output=output)
    invariance = run_invariance_v2(raw, repeats=args.repeats)
    validator = build_validator_summary_v2(output=output, hashes=hashes, artifact_refs=[])
    receipts = write_receipt_artifacts(output=output, invariance=invariance, validator_summary=validator, out_dir=args.out_dir)

    validator["artifact_refs"] = [receipts["runtime_artifact"], receipts["invariance_artifact"]]
    Path(receipts["validator_artifact"]).write_text(json.dumps(validator, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        **receipts,
        "hashes": hashes,
        "runtime_hash": sha256_hex(canonical_json(output)),
        "invariance_status": invariance["status"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
