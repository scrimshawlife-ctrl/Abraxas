from __future__ import annotations

from dataclasses import dataclass


AUTHORITY_FLAGS = {
    "overlay_application": False,
    "baseline_mutation": False,
    "runtime_config_write": False,
    "promotion": False,
    "execution": False,
    "scheduler": False,
}


@dataclass(frozen=True)
class SimulationCoverage:
    forecasts_matched: int
    scores_used: int


@dataclass(frozen=True)
class SimulationResult:
    overlay_id: str
    source_key: str
    status: str
    baseline_error: float | None
    simulated_error: float | None
    delta_error: float | None
    improvement_direction: str | None
    coverage: SimulationCoverage
    reason: str | None

    def to_dict(self) -> dict:
        return {
            "simulation_version": "CanaryOverlaySimulation.v1",
            "overlay_id": self.overlay_id,
            "source_key": self.source_key,
            "status": self.status,
            "baseline_error": self.baseline_error,
            "simulated_error": self.simulated_error,
            "delta_error": self.delta_error,
            "improvement_direction": self.improvement_direction,
            "coverage": {
                "forecasts_matched": self.coverage.forecasts_matched,
                "scores_used": self.coverage.scores_used,
            },
            "reason": self.reason,
            "authority": dict(AUTHORITY_FLAGS),
        }
