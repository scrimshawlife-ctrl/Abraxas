from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def build_projection(registry_path: Path) -> dict[str, Any]:
    if not registry_path.exists():
        raise FileNotFoundError(f"missing registry: {registry_path}")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    required = {"combined_status", "pointer_closure", "drift_class", "repo_proof", "runtime_proof"}
    if not required.issubset(registry.keys()):
        raise ValueError("invalid registry: missing required keys")

    return {
        "schema": "ProofStateProjection.v1",
        "combined_status": registry["combined_status"],
        "pointer_closure": registry["pointer_closure"],
        "drift_class": registry["drift_class"],
        "proof_layers": {
            "repo": "PRESENT" if registry.get("repo_proof") else "MISSING",
            "runtime": "PRESENT" if registry.get("runtime_proof") else "MISSING",
            "registry": "BOUND",
        },
        "authority": {
            "projection_only": True,
            "promotion_allowed": False,
            "runtime_mutation": False,
            "forecast_influence": False,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="out/proof/proof_registry.latest.json")
    ap.add_argument("--output", default="out/viz/proof_state.latest.json")
    args = ap.parse_args()

    projection = build_projection(Path(args.registry))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(canonical_json(projection), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
