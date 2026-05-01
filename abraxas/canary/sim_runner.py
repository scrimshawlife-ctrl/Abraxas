from __future__ import annotations

from typing import Any

from abraxas.canary.sim_models import AUTHORITY_FLAGS
from abraxas.canary.simulation import run_overlay_simulation
from abraxas.canary.sim_validator import validate_simulation_run


def build_canary_overlay_simulation_run(
    overlay_run: dict[str, Any],
    forecast_run: dict[str, Any],
    outcome_run: dict[str, Any],
    score_run: dict[str, Any],
) -> dict[str, Any]:
    simulations = run_overlay_simulation(overlay_run, forecast_run, outcome_run, score_run)
    computed = sum(1 for s in simulations if s.get("status") == "computed")
    not_computable = sum(1 for s in simulations if s.get("status") == "not_computable")
    report = {
        "artifact": "CANARY-OVERLAY-SIMULATION-001",
        "schema_version": "CanaryOverlaySimulationRun.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "counts": {
            "overlays_total": len(simulations),
            "computed": computed,
            "not_computable": not_computable,
        },
        "simulations": simulations,
    }
    validate_simulation_run(report)
    return report
