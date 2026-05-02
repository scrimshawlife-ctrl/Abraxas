from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def _health(combined_status: str, pointer_closure: str) -> str:
    if combined_status == "LOCAL_CHAIN_PROVEN" and pointer_closure == "PASS":
        return "GREEN"
    if pointer_closure != "PASS":
        return "RED"
    return "YELLOW"


def build_status_card(projection_path: Path, timestamp: str = "2026-05-01T00:00:00Z") -> dict[str, Any]:
    if not projection_path.exists():
        raise FileNotFoundError(f"missing projection: {projection_path}")
    projection = json.loads(projection_path.read_text(encoding="utf-8"))
    required = {"schema", "combined_status", "pointer_closure", "drift_class", "proof_layers", "authority"}
    if not required.issubset(projection):
        raise ValueError("invalid projection schema")

    combined_status = projection["combined_status"]
    pointer_closure = projection["pointer_closure"]
    health = _health(combined_status, pointer_closure)

    layer_src = projection.get("proof_layers", {})
    layers = {
        "repo": "OK" if layer_src.get("repo") == "PRESENT" else "MISSING",
        "runtime": "OK" if layer_src.get("runtime") == "PRESENT" else "MISSING",
        "registry": "OK" if layer_src.get("registry") == "BOUND" else "MISSING",
        "projection": "OK",
    }

    alerts = []
    if health != "GREEN":
        alerts.append("PROOF_CHAIN_ATTENTION_REQUIRED")

    return {
        "schema": "ProofStatusCard.v1",
        "status": combined_status,
        "health": health,
        "pointer_closure": pointer_closure,
        "drift_class": projection["drift_class"],
        "layers": layers,
        "authority": {
            "can_promote": False,
            "can_mutate_runtime": False,
            "can_influence_forecast": False,
            "mode": "OBSERVE_ONLY",
        },
        "alerts": alerts,
        "recommended_next_action": "PREPARE_CANARY_LAYER" if health == "GREEN" else "RESOLVE_PROOF_CHAIN",
        "timestamp": timestamp,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="out/viz/proof_state.latest.json")
    ap.add_argument("--output", default="out/operator/proof_status_card.latest.json")
    ap.add_argument("--timestamp", default="2026-05-01T00:00:00Z")
    args = ap.parse_args()

    card = build_status_card(Path(args.input), args.timestamp)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(canonical_json(card), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
