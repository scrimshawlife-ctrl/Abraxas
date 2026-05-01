from __future__ import annotations

from hashlib import sha256
from typing import Any

from abraxas.core.canonical import canonical_json
from abraxas.canary.sim_models import SimulationCoverage, SimulationResult


def _r6(value: float) -> float:
    return round(float(value), 6)


def _overlay_id(overlay: dict[str, Any]) -> str:
    if isinstance(overlay.get("overlay_id"), str) and overlay["overlay_id"]:
        return overlay["overlay_id"]
    return sha256(canonical_json(overlay).encode("utf-8")).hexdigest()


def _extract_overlays(overlay_run: dict[str, Any]) -> list[dict[str, Any]]:
    overlays = overlay_run.get("overlays")
    return overlays if isinstance(overlays, list) else []


def _extract_forecasts(forecast_run: dict[str, Any]) -> list[dict[str, Any]]:
    forecasts = forecast_run.get("forecasts")
    return forecasts if isinstance(forecasts, list) else []


def _extract_scores(score_run: dict[str, Any]) -> list[dict[str, Any]]:
    scores = score_run.get("scores")
    return scores if isinstance(scores, list) else []


def _forecast_matches_source(forecast: dict[str, Any], source_key: str) -> bool:
    signal_sources = forecast.get("signal_sources")
    source_families = forecast.get("source_families")
    sources = signal_sources if isinstance(signal_sources, list) else []
    families = source_families if isinstance(source_families, list) else []
    return source_key in sources or source_key in families


def _sim_delta(overlay: dict[str, Any]) -> float:
    raw = overlay.get("simulated_delta", overlay.get("weight_delta", overlay.get("delta", 0.0)))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def run_overlay_simulation(
    overlay_run: dict[str, Any],
    forecast_run: dict[str, Any],
    _outcome_run: dict[str, Any],
    score_run: dict[str, Any],
) -> list[dict[str, Any]]:
    forecasts = _extract_forecasts(forecast_run)
    scores = _extract_scores(score_run)
    score_by_forecast = {
        str(item.get("forecast_id")): item
        for item in scores
        if isinstance(item, dict) and item.get("forecast_id") is not None
    }

    results: list[dict[str, Any]] = []
    for overlay in _extract_overlays(overlay_run):
        source_key = str(overlay.get("source_key", ""))
        overlay_id = _overlay_id(overlay)

        matched_forecast_ids = [
            str(f.get("forecast_id"))
            for f in forecasts
            if isinstance(f, dict)
            and f.get("forecast_id") is not None
            and _forecast_matches_source(f, source_key)
        ]

        if not matched_forecast_ids:
            results.append(
                SimulationResult(
                    overlay_id=overlay_id,
                    source_key=source_key,
                    status="not_computable",
                    baseline_error=None,
                    simulated_error=None,
                    delta_error=None,
                    improvement_direction=None,
                    coverage=SimulationCoverage(forecasts_matched=0, scores_used=0),
                    reason="no_matching_forecasts",
                ).to_dict()
            )
            continue

        briers: list[float] = []
        for forecast_id in matched_forecast_ids:
            row = score_by_forecast.get(forecast_id)
            if row is None:
                continue
            value = row.get("brier_score", row.get("brier"))
            try:
                briers.append(float(value))
            except (TypeError, ValueError):
                continue

        if not briers:
            results.append(
                SimulationResult(
                    overlay_id=overlay_id,
                    source_key=source_key,
                    status="not_computable",
                    baseline_error=None,
                    simulated_error=None,
                    delta_error=None,
                    improvement_direction=None,
                    coverage=SimulationCoverage(
                        forecasts_matched=len(matched_forecast_ids), scores_used=0
                    ),
                    reason="no_scores_available",
                ).to_dict()
            )
            continue

        baseline = _r6(sum(briers) / len(briers))
        delta = _sim_delta(overlay)
        simulated = _r6(sum((b * (1.0 + delta)) for b in briers) / len(briers))
        diff = _r6(simulated - baseline)

        direction = "neutral"
        if diff < 0:
            direction = "improved"
        elif diff > 0:
            direction = "worsened"

        results.append(
            SimulationResult(
                overlay_id=overlay_id,
                source_key=source_key,
                status="computed",
                baseline_error=baseline,
                simulated_error=simulated,
                delta_error=diff,
                improvement_direction=direction,
                coverage=SimulationCoverage(
                    forecasts_matched=len(matched_forecast_ids), scores_used=len(briers)
                ),
                reason=None,
            ).to_dict()
        )

    return sorted(results, key=lambda x: (x["source_key"], x["overlay_id"]))
