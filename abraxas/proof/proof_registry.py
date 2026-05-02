from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_registry(
    repo_dir: Path = Path("out/proof/repo"),
    runtime_path: Path = Path("out/proofs/proof_artifact_001.latest.json"),
) -> dict[str, Any]:
    repo_proof = {
        "repo_proof_manifest": _load_json(repo_dir / "repo_proof_manifest.latest.json"),
        "patch_coverage_map": _load_json(repo_dir / "patch_coverage_map.latest.json"),
        "repo_canon_alignment_report": _load_json(repo_dir / "repo_canon_alignment_report.latest.json"),
        "repo_proof_receipt": _load_json(repo_dir / "repo_proof_receipt.latest.json"),
    }
    runtime_proof = _load_json(runtime_path)

    drift_class = repo_proof["repo_canon_alignment_report"].get("drift_class", "not_computable")
    pointer_closure = runtime_proof.get("validation", {}).get("pointer_closure_status", "FAIL")

    authority_flags_false = (
        runtime_proof.get("lane") == "SHADOW"
        and all(v is False for v in runtime_proof.get("authority", {}).values())
        and repo_proof["repo_proof_receipt"].get("authority_boundary") == "proof_only"
        and repo_proof["repo_proof_receipt"].get("promotion_granted") is False
        and repo_proof["repo_proof_receipt"].get("runtime_mutation") is False
    )

    combined_status = "LOCAL_CHAIN_PROVEN" if pointer_closure == "PASS" and authority_flags_false else "NOT_COMPUTABLE"

    return {
        "schema": "ProofRegistry.v1",
        "repo_proof": repo_proof,
        "runtime_proof": runtime_proof,
        "combined_status": combined_status,
        "drift_class": drift_class,
        "pointer_closure": pointer_closure,
        "authority_boundary": "proof_only",
        "promotion_granted": False,
        "runtime_mutation": False,
        "scheduler_write": False,
        "forecast_influence": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-dir", default="out/proof/repo")
    ap.add_argument("--runtime-proof", default="out/proofs/proof_artifact_001.latest.json")
    ap.add_argument("--output", default="out/proof/proof_registry.latest.json")
    args = ap.parse_args()

    registry = build_registry(Path(args.repo_dir), Path(args.runtime_proof))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(canonical_json(registry), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
