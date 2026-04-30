#!/usr/bin/env python3
"""Run PATCH-004 meta-governance bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.governance.attestation_runner import run_attestation
from abraxas.governance.binding_validator import validate_bindings
from abraxas.governance.repair_suggester import suggest_repairs


def build_bundle(repo_root: Path, timestamp: str) -> dict:
    attestation = run_attestation(repo_root=repo_root, timestamp=timestamp)
    binding_validation = validate_bindings(repo_root=repo_root)
    repair_suggestions = suggest_repairs(binding_validation)

    statuses = [attestation["status"], binding_validation["status"], repair_suggestions["status"]]
    status = "PASS"
    if "FAIL" in statuses:
        status = "FAIL"
    elif "PARTIAL" in statuses:
        status = "PARTIAL"

    return {
        "schema_version": "Patch004MetaGovernanceBundle.v1",
        "attestation": attestation,
        "binding_validation": binding_validation,
        "repair_suggestions": repair_suggestions,
        "status": status,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default="out/reports/patch004_meta_governance.latest.json")
    parser.add_argument("--timestamp", default="1970-01-01T00:00:00Z")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    bundle = build_bundle(repo_root, args.timestamp)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = repo_root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path.as_posix())


if __name__ == "__main__":
    main()
