"""
Scenario Envelope Runner: Type Definitions

Defines data structures for scenario-based forecasting driven by simulation priors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ScenarioInput:
    """
    Input bundle for scenario envelope generation.

    Captures snapshot of priors, weather, and context at run time.
    """

    run_id: str
    timestamp: str  # ISO 8601
    sim_priors: Dict[str, float]  # From sim_adapter or CLI overrides
    current_weather: Optional[Dict[str, Any]] = None
    dm_snapshot: Optional[Dict[str, Any]] = None  # D/M metrics snapshot
    almanac_snapshot: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class ScenarioEnvelope:
    """
    Single scenario envelope with label, priors, and outputs.

    Represents one configuration of simulation knobs (e.g., high_MRI, baseline).
    """

    label: str  # "baseline", "high_MRI", "high_IRI", "long_tau"
    priors: Dict[str, float]  # Modified knobs for this envelope
    outputs: Dict[str, Any]  # NCP/CNF/EFTE results merged
    confidence: str  # LOW/MED/HIGH
    falsifiers: List[str]  # Conditions that would invalidate this envelope


@dataclass(frozen=True)
class ScenarioRunResult:
    """
    Complete scenario run result with all envelopes and provenance.

    Deterministic output from scenario envelope runner.
    """

    input: ScenarioInput
    envelopes: List[ScenarioEnvelope]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "input": {
                "run_id": self.input.run_id,
                "timestamp": self.input.timestamp,
                "sim_priors": self.input.sim_priors,
                "current_weather": self.input.current_weather,
                "dm_snapshot": self.input.dm_snapshot,
                "almanac_snapshot": self.input.almanac_snapshot,
                "notes": self.input.notes,
            },
            "envelopes": [
                {
                    "label": env.label,
                    "priors": env.priors,
                    "outputs": env.outputs,
                    "confidence": env.confidence,
                    "falsifiers": env.falsifiers,
                }
                for env in self.envelopes
            ],
            "provenance": self.provenance,
        }
