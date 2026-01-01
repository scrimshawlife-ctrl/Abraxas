"""Abraxas Simulation Architecture

Full deterministic simulation system with:
- Network dynamics (graphs, communities, link prediction)
- Game-theoretic media actors (strategic misinformation)
- Quantum-inspired operators (community detection, link prediction)
- Temporal correlations (state-over-time)
- Two-layer reality (world + media)

IMMUTABLE LAWS:
1. No Metric Without Simulation
2. No Simulation Without Runes
3. Determinism First
4. Provenance Always
5. Complexity Pays Rent

ARCHITECTURE:
- Metric Registry: All metrics (observations)
- SimVar Registry: All simulation variables (latent state)
- Rune Registry: Mandatory couplers (metrics ⇄ variables)
- Outcome Ledger: Append-only log of results
"""

from abraxas.simulation.registries.metric_registry import MetricDefinition, MetricRegistry
from abraxas.simulation.registries.rune_registry import RuneBinding, RuneRegistry
from abraxas.simulation.registries.simvar_registry import SimVarDefinition, SimVarRegistry
from abraxas.simulation.registries.outcome_ledger import OutcomeLedger, OutcomeEntry
from abraxas.simulation.validation import SimulationValidator, run_startup_gate
from abraxas.simulation.add_metric import MetricAdditionPipeline, bump_semantic_version

__all__ = [
    # Registries
    "MetricRegistry",
    "SimVarRegistry",
    "RuneRegistry",
    "OutcomeLedger",
    # Definitions
    "MetricDefinition",
    "SimVarDefinition",
    "RuneBinding",
    "OutcomeEntry",
    # Validation
    "SimulationValidator",
    "run_startup_gate",
    # Utilities
    "MetricAdditionPipeline",
    "bump_semantic_version",
]
