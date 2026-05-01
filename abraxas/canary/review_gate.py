from __future__ import annotations

from hashlib import sha256
from typing import Any

from abraxas.canary.review_models import AUTHORITY_FLAGS, THRESHOLDS, Recommendation
from abraxas.core.canonical import canonical_json


def _sha_obj(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _evaluate(sim: dict[str, Any]) -> tuple[str, str]:
    sim_status = str(sim.get("status", ""))
    sim_reason = sim.get("reason") or "unknown"
    if sim_status != "computed":
        return "not_computable", f"simulation_not_computable:{sim_reason}"

    coverage = sim.get("coverage") if isinstance(sim.get("coverage"), dict) else {}
    scores_used = int(coverage.get("scores_used", 0))
    delta_error = sim.get("delta_error")
    if scores_used < THRESHOLDS["min_scores_used"]:
        return "recommend_hold", "insufficient_scores_used"
    if delta_error is not None and float(delta_error) <= THRESHOLDS["min_improvement_delta"]:
        return "recommend_approve_for_activation_review", "meets_improvement_threshold"
    if delta_error is not None and float(delta_error) > THRESHOLDS["max_worsening_delta"]:
        return "recommend_reject", "exceeds_worsening_threshold"
    return "recommend_hold", "neutral_or_insufficient_improvement"


def build_recommendations(
    simulation_run: dict[str, Any],
    overlay_run: dict[str, Any],
    ledger_run: dict[str, Any],
) -> list[dict[str, Any]]:
    simulations = simulation_run.get("simulations") if isinstance(simulation_run.get("simulations"), list) else []
    overlays = overlay_run.get("overlays") if isinstance(overlay_run.get("overlays"), list) else []
    entries = ledger_run.get("entries") if isinstance(ledger_run.get("entries"), list) else []

    overlay_by_id = {str(o.get("overlay_id")): o for o in overlays if isinstance(o, dict) and o.get("overlay_id")}
    ledger_by_entry_id = {str(e.get("entry_id")): e for e in entries if isinstance(e, dict) and e.get("entry_id")}

    ordered_sims = sorted(
        (s for s in simulations if isinstance(s, dict)),
        key=lambda s: (str(s.get("source_key", "")), str(s.get("overlay_id", ""))),
    )

    recs: list[dict[str, Any]] = []
    for sim in ordered_sims:
        overlay_id = str(sim.get("overlay_id", ""))
        source_key = str(sim.get("source_key", ""))
        overlay = overlay_by_id.get(overlay_id)

        simulation_hash = _sha_obj(sim)
        basis_coverage = sim.get("coverage") if isinstance(sim.get("coverage"), dict) else {}
        basis = {
            "simulation_status": sim.get("status"),
            "baseline_error": sim.get("baseline_error"),
            "simulated_error": sim.get("simulated_error"),
            "delta_error": sim.get("delta_error"),
            "improvement_direction": sim.get("improvement_direction"),
            "forecasts_matched": int(basis_coverage.get("forecasts_matched", 0)),
            "scores_used": int(basis_coverage.get("scores_used", 0)),
        }

        if overlay is None:
            status = "not_computable"
            reason = "missing_overlay"
            entry_id = None
            proposal_id = None
            ledger_hash = None
        else:
            entry_id = str(overlay.get("entry_id")) if overlay.get("entry_id") is not None else None
            proposal_id = str(overlay.get("proposal_id")) if overlay.get("proposal_id") is not None else None
            status, reason = _evaluate(sim)
            ledger_entry = ledger_by_entry_id.get(entry_id or "") if entry_id else None
            ledger_hash = _sha_obj(ledger_entry) if ledger_entry is not None else None
            if ledger_hash is None:
                reason = f"{reason}|missing_ledger_entry"

        lineage = {
            "overlay_id": overlay_id,
            "simulation_hash": simulation_hash,
            "ledger_entry_hash": ledger_hash,
            "proposal_id": proposal_id,
        }

        base_payload = {
            "recommendation_version": "CanaryReviewRecommendation.v1",
            "overlay_id": overlay_id,
            "entry_id": entry_id,
            "proposal_id": proposal_id,
            "source_key": source_key,
            "status": status,
            "basis": basis,
            "thresholds": dict(THRESHOLDS),
            "reason": reason,
            "lineage": lineage,
            "authority": dict(AUTHORITY_FLAGS),
        }
        recommendation_id = _sha_obj(base_payload)
        recs.append(
            Recommendation(
                recommendation_id=recommendation_id,
                overlay_id=overlay_id,
                entry_id=entry_id,
                proposal_id=proposal_id,
                source_key=source_key,
                status=status,
                basis=basis,
                reason=reason,
                lineage=lineage,
            ).to_dict()
        )

    return sorted(recs, key=lambda r: (r["source_key"], r["recommendation_id"]))
