"""
Scenario Envelope Runner

Orchestrates scenario envelope generation and execution.
Deterministic; no simulation engine required (uses adapter pattern).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

from abraxas.scenario.envelopes import build_envelopes
from abraxas.scenario.types import ScenarioEnvelope, ScenarioInput, ScenarioRunResult


def compute_confidence(priors: Dict[str, float], context: Dict[str, Any]) -> str:
    """
    Compute confidence level deterministically.

    Rules:
    - HIGH: All 4 knobs present (MRI, IRI, tau_memory, tau_latency) AND 2+ sources
    - MED: All 4 knobs present but only 1 source
    - LOW: Otherwise

    Args:
        priors: Simulation priors dictionary
        context: Additional context (may contain source count)

    Returns:
        Confidence string: "HIGH", "MED", or "LOW"
    """
    required_knobs = {"MRI", "IRI", "tau_memory", "tau_latency"}
    has_all_knobs = all(knob in priors for knob in required_knobs)

    source_count = context.get("source_count", 0)

    if has_all_knobs and source_count >= 2:
        return "HIGH"
    elif has_all_knobs and source_count >= 1:
        return "MED"
    else:
        return "LOW"


def run_scenarios(
    base_priors: Dict[str, float],
    sod_runner: Callable[[Dict[str, Any], Dict[str, float]], Dict[str, Any]],
    context: Dict[str, Any],
) -> ScenarioRunResult:
    """
    Run scenario envelope analysis.

    Generates envelopes from base priors, executes SOD bundle for each envelope,
    and packages results with provenance.

    Args:
        base_priors: Base simulation priors
        sod_runner: Callable that executes SOD bundle (NCP/CNF/EFTE)
        context: Additional context (weather, D/M snapshot, etc.)

    Returns:
        ScenarioRunResult with all envelopes and provenance
    """

    # Generate run ID and timestamp
    run_id = context.get("run_id", f"scenario_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")
    timestamp = context.get("timestamp") or context.get("timestamp_utc") or datetime.now(timezone.utc).isoformat()

    # Build scenario input
    scenario_input = ScenarioInput(
        run_id=run_id,
        timestamp=timestamp,
        sim_priors=base_priors,
        current_weather=context.get("weather"),
        dm_snapshot=context.get("dm_snapshot"),
        almanac_snapshot=context.get("almanac_snapshot"),
        notes=context.get("notes"),
    )

    # Generate envelope configurations
    envelope_configs = build_envelopes(base_priors)

    # Execute SOD runner for each envelope
    executed_envelopes: List[ScenarioEnvelope] = []

    for config in envelope_configs:
        label = config["label"]
        priors = config["priors"]
        falsifiers = config["falsifiers"]

        # Run SOD bundle with envelope-specific priors
        sod_outputs = sod_runner(context, priors)

        # Compute confidence
        confidence = compute_confidence(priors, context)

        # Create envelope
        envelope = ScenarioEnvelope(
            label=label,
            priors=priors,
            outputs=sod_outputs,
            confidence=confidence,
            falsifiers=falsifiers,
        )

        executed_envelopes.append(envelope)

    # Build provenance
    provenance = {
        "generator": "scenario_envelope_runner",
        "version": "1.0.0",
        "timestamp": timestamp,
        "base_priors_hash": hash(frozenset(base_priors.items())),
        "envelope_count": len(executed_envelopes),
    }

    # Package result
    result = ScenarioRunResult(
        input=scenario_input,
        envelopes=executed_envelopes,
        provenance=provenance,
    )

    return result
