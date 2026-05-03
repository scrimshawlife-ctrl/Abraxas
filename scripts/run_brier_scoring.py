from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import Any

from abraxas.semantic.contracts import ContractLoadError, canonical_hash, load_contract


def _load_contract(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        return load_contract(path, "ForecastOutcomeSet.v1"), None
    except ContractLoadError as exc:
        return {}, exc.reason


def main() -> None:
    data, reason = _load_contract(Path("out/scoring/forecast_outcome_set.latest.json"))
    forecasts = data.get("forecasts", []) if isinstance(data.get("forecasts"), list) else []
    outcomes = data.get("outcomes", []) if isinstance(data.get("outcomes"), list) else []
    outcome_map = {str(o.get("forecast_id")): o for o in outcomes if isinstance(o, dict) and o.get("forecast_id") is not None}

    scored: list[dict[str, Any]] = []
    unresolved = 0
    for f in forecasts:
        if not isinstance(f, dict):
            unresolved += 1
            continue
        fid = str(f.get("id", ""))
        prob = f.get("probability")
        out = outcome_map.get(fid, {})
        outcome = out.get("resolved_value")
        if not fid or f.get("label") not in ("YES", "NO") or not isinstance(prob, (int, float)) or prob < 0 or prob > 1 or outcome not in (0, 1):
            unresolved += 1
            continue
        brier = float((float(prob) - int(outcome)) ** 2)
        scored.append({"forecast_id": fid, "probability": float(prob), "outcome": int(outcome), "brier_score": brier})

    status = "COMPUTABLE" if scored else "NOT_COMPUTABLE"
    payload: dict[str, Any] = {
        "schema_version": "BrierScoringRun.v1",
        "status": status,
        "reason": None if scored else (reason or "MISSING_OR_INVALID_SCOREABLE_INPUT"),
        "scored_count": len(scored),
        "unresolved_count": unresolved,
        "mean_brier": (sum(s["brier_score"] for s in scored) / len(scored)) if scored else None,
        "scores": scored,
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    payload["packet_hash"] = canonical_hash(payload)
    out_path = Path("out/scoring/brier_scoring.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
