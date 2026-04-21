from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.runes.gap_closure.runtime import load_json, write_canonical_json
from abraxas.runes.gap_closure.validator import validate_gap_closure_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate gap closure artifacts for one run id.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir or Path("artifacts_seal/runs") / args.run_id
    index_path = run_dir / "artifact_index.json"
    artifact_index = load_json(index_path).get("artifacts", []) if index_path.exists() else []

    report = validate_gap_closure_artifacts(run_id=args.run_id, run_dir=run_dir, artifact_index=artifact_index)
    report_hash = write_canonical_json(run_dir / "closure_validation_report.json", report)
    validator_payload = {
        "schema_version": "gap_closure.validator.v1",
        "run_id": args.run_id,
        "report_path": (run_dir / "closure_validation_report.json").as_posix(),
        "report_hash": report_hash,
        "status": report["status"],
        "promotion_decision": report["promotion_decision"],
    }
    out_path = Path("out/validators") / f"{args.run_id}.gap_closure.validator.json"
    write_canonical_json(out_path, validator_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
