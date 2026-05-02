from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def build_canary_readiness(card_path: Path) -> dict[str, Any]:
    if not card_path.exists():
        raise FileNotFoundError(f"missing operator card: {card_path}")
    card = json.loads(card_path.read_text(encoding="utf-8"))
    required = {"schema", "status", "health", "pointer_closure", "authority"}
    if not required.issubset(card):
        raise ValueError("invalid operator card schema")

    authority_mode = card.get("authority", {}).get("mode")
    ready = (
        card.get("health") == "GREEN"
        and card.get("pointer_closure") == "PASS"
        and authority_mode == "OBSERVE_ONLY"
    )

    blockers: list[str] = []
    if card.get("health") != "GREEN":
        blockers.append("HEALTH_NOT_GREEN")
    if card.get("pointer_closure") != "PASS":
        blockers.append("POINTER_CLOSURE_NOT_PASS")
    if authority_mode != "OBSERVE_ONLY":
        blockers.append("AUTHORITY_MODE_INVALID")

    return {
        "schema": "CanaryReadiness.v1",
        "canary_ready": ready,
        "reason": "All proof layers validated, pointer closure PASS, system stable." if ready else "Readiness blocked by proof or authority constraints.",
        "blocked": not ready,
        "blockers": blockers,
        "next_step": "CANARY_SIMULATION_ONLY",
        "authority": {
            "can_activate_canary": False,
            "can_mutate_runtime": False,
            "mode": "READINESS_ONLY",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="out/operator/proof_status_card.latest.json")
    ap.add_argument("--output", default="out/operator/canary_readiness.latest.json")
    args = ap.parse_args()

    readiness = build_canary_readiness(Path(args.input))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(canonical_json(readiness), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
