"""END-TO-END EXEMPLAR: Media Competition Misinformation Pressure

This exemplar demonstrates the full Abraxas simulation architecture with:
- Network dynamics (graph, communities, link prediction)
- Game-theoretic media actors (strategy profiles, payoffs)
- Quantum-inspired operators (community detection, link prediction)
- Temporal correlations (state-over-time)
- Conformity/peer pressure
- Two-layer reality (world + media)

METRIC: MEDIA_COMPETITION_MISINFO_PRESSURE
Measures misinformation pressure from competing media actors in a network setting.

TRAINING DATA SOURCE: SML Paper Registry
Uses parameters from ARXIV_SPATIAL_GAMES and related game-theoretic papers.
"""

from __future__ import annotations

from datetime import datetime

from abraxas.simulation.registries.metric_registry import (
    MetricDefinition,
    MetricProvenance,
)
from abraxas.simulation.registries.rune_registry import (
    ManipulationModel,
    NoiseModel,
    ObserverModel,
    ProvenanceManifest,
    RuneBinding,
    TransitionModel,
    VarTarget,
)
from abraxas.simulation.registries.simvar_registry import (
    EvolutionModel,
    PriorDistribution,
    SimVarDefinition,
)

# ==============================================================================
# METRIC DEFINITION
# ==============================================================================

METRIC_MEDIA_COMPETITION = MetricDefinition(
    metric_id="MEDIA_COMPETITION_MISINFO_PRESSURE",
    version="1.0.0",
    description=(
        "Measures misinformation pressure from competing media actors. "
        "Accounts for network topology, community structure, strategic "
        "misinformation deployment, conformity pressure, and temporal dynamics."
    ),
    metric_class="media_competition",
    units="dimensionless",
    valid_range={"min": 0.0, "max": 1.0},
    decay_half_life=24.0,  # 24 hours
    dependencies=[],
    adversarial_risk=0.85,  # High manipulation risk
    layer_scope=["world", "media"],  # Observes both layers
    provenance=MetricProvenance(
        created=datetime.utcnow().isoformat() + "Z",
        source="abraxas_simulation_architect",
        paper_refs=["ARXIV_SPATIAL_GAMES", "PMC10924450"],  # From SML registry
    ),
)

# ==============================================================================
# SIMULATION VARIABLES (All Layers + Classes)
# ==============================================================================

# --- WORLD LAYER: Belief State ---
VAR_PUBLIC_OPINION = SimVarDefinition(
    var_id="public_opinion_belief_state",
    version="1.0.0",
    var_class="belief_state",
    var_type="continuous",
    bounds={"min": -1.0, "max": 1.0},  # -1 = full disbelief, +1 = full belief
    prior_distribution=PriorDistribution(
        distribution_type="normal",
        parameters={"mean": 0.0, "stddev": 0.3},
        sml_source={
            "paper_id": "ARXIV_SPATIAL_GAMES",
            "knob_mapping": "Initial belief distribution from game-theoretic equilibrium",
            "confidence": "HIGH",
        },
    ),
    evolution_model=EvolutionModel(
        update_rule="opinion_dynamics",
        deterministic=True,
        parameters={"update_rate": 0.1, "influence_weight": 0.5},
    ),
    coupling_capacity={
        "max_runes": 5,
        "allowed_metric_classes": [
            "manipulation_risk",
            "media_competition",
            "opinion_distribution",
        ],
    },
    layer="world",
    provenance={"created": datetime.utcnow().isoformat() + "Z", "source": "exemplar"},
)

# --- MEDIA LAYER: Context Operator ---
VAR_FRAMING_CONTEXT = SimVarDefinition(
    var_id="media_framing_context",
    version="1.0.0",
    var_class="context_operator",
    var_type="continuous",
    bounds={"min": 0.0, "max": 1.0},  # Framing intensity
    prior_distribution=PriorDistribution(
        distribution_type="uniform",
        parameters={"min": 0.0, "max": 1.0},
    ),
    evolution_model=EvolutionModel(
        update_rule="custom",
        deterministic=True,
        parameters={"context_shift_rate": 0.05},
    ),
    coupling_capacity={
        "max_runes": 3,
        "allowed_metric_classes": ["media_competition", "manipulation_risk"],
    },
    layer="media",
    provenance={"created": datetime.utcnow().isoformat() + "Z", "source": "exemplar"},
)

# --- MEDIA LAYER: Media Actor State ---
VAR_MEDIA_CREDIBILITY = SimVarDefinition(
    var_id="media_actor_credibility",
    version="1.0.0",
    var_class="media_actor_state",
    var_type="continuous",
    bounds={"min": 0.0, "max": 1.0},  # Credibility score
    prior_distribution=PriorDistribution(
        distribution_type="beta",
        parameters={"alpha": 2.0, "beta": 2.0},  # Slightly biased toward middle
    ),
    evolution_model=EvolutionModel(
        update_rule="game_theoretic",
        deterministic=True,
        parameters={"reputation_decay": 0.01, "truth_bonus": 0.1},
    ),
    coupling_capacity={
        "max_runes": 3,
        "allowed_metric_classes": ["media_competition", "strategic_behavior"],
    },
    layer="media",
    provenance={"created": datetime.utcnow().isoformat() + "Z", "source": "exemplar"},
)

# --- MEDIA LAYER: Strategy Profile ---
VAR_MISINFO_STRATEGY = SimVarDefinition(
    var_id="misinformation_strategy_mix",
    version="1.0.0",
    var_class="strategy_profile",
    var_type="continuous",
    bounds={"min": 0.0, "max": 1.0},  # 0 = all truth, 1 = all misinfo
    prior_distribution=PriorDistribution(
        distribution_type="uniform",
        parameters={"min": 0.0, "max": 0.3},  # Most actors start with low misinfo
        sml_source={
            "paper_id": "ARXIV_SPATIAL_GAMES",
            "knob_mapping": "MRI from effort parameter (propagandist strategy)",
            "confidence": "HIGH",
        },
    ),
    evolution_model=EvolutionModel(
        update_rule="strategy_adapt",
        deterministic=True,
        parameters={"adaptation_rate": 0.05, "payoff_sensitivity": 0.2},
    ),
    coupling_capacity={
        "max_runes": 3,
        "allowed_metric_classes": ["media_competition", "strategic_behavior"],
    },
    layer="media",
    provenance={"created": datetime.utcnow().isoformat() + "Z", "source": "exemplar"},
)

# --- WORLD LAYER: Network State ---
VAR_SOCIAL_NETWORK = SimVarDefinition(
    var_id="social_network_graph",
    version="1.0.0",
    var_class="network_state",
    var_type="graph",
    bounds={"shape": [1000, 1000]},  # 1000 nodes, adjacency matrix
    prior_distribution=PriorDistribution(
        distribution_type="graph_barabasi_albert",
        parameters={"n": 1000, "m": 3},  # Scale-free network
    ),
    evolution_model=EvolutionModel(
        update_rule="network_rewiring",
        deterministic=True,
        parameters={"rewire_prob": 0.01, "homophily_factor": 0.3},
    ),
    coupling_capacity={
        "max_runes": 5,
        "allowed_metric_classes": [
            "network_topology",
            "community_structure",
            "opinion_distribution",
        ],
    },
    layer="world",
    provenance={"created": datetime.utcnow().isoformat() + "Z", "source": "exemplar"},
)

# --- WORLD LAYER: Community Structure (Quantum-Inspired Optimization) ---
VAR_COMMUNITIES = SimVarDefinition(
    var_id="community_assignment",
    version="1.0.0",
    var_class="community_structure",
    var_type="categorical",
    bounds={"categories": [f"community_{i}" for i in range(10)]},  # 10 communities
    prior_distribution=PriorDistribution(
        distribution_type="custom",
        parameters={"initial_assignment": "spectral_clustering"},
    ),
    evolution_model=EvolutionModel(
        update_rule="quantum_inspired_optimization",  # QUBO-style community detection
        deterministic=True,
        parameters={"modularity_weight": 1.0, "stability_penalty": 0.1},
    ),
    coupling_capacity={
        "max_runes": 3,
        "allowed_metric_classes": ["community_structure", "network_topology"],
    },
    layer="world",
    provenance={"created": datetime.utcnow().isoformat() + "Z", "source": "exemplar"},
)

# --- WORLD LAYER: Link Probability Field (Quantum-Walk Inspired) ---
VAR_LINK_PREDICTION = SimVarDefinition(
    var_id="link_probability_field",
    version="1.0.0",
    var_class="link_probability_field",
    var_type="matrix",
    bounds={"shape": [1000, 1000]},  # Probability matrix for all node pairs
    prior_distribution=PriorDistribution(
        distribution_type="uniform",
        parameters={"min": 0.0, "max": 0.1},  # Low initial probabilities
    ),
    evolution_model=EvolutionModel(
        update_rule="quantum_walk",  # Multi-hop propagation with interference
        deterministic=True,
        parameters={"walk_steps": 3, "interference_decay": 0.9},
    ),
    coupling_capacity={
        "max_runes": 2,
        "allowed_metric_classes": ["network_topology"],
    },
    layer="world",
    provenance={"created": datetime.utcnow().isoformat() + "Z", "source": "exemplar"},
)

# --- WORLD LAYER: Conformity Pressure ---
VAR_CONFORMITY = SimVarDefinition(
    var_id="conformity_pressure_field",
    version="1.0.0",
    var_class="conformity_pressure",
    var_type="continuous",
    bounds={"min": 0.0, "max": 1.0},  # Per-node conformity pressure
    prior_distribution=PriorDistribution(
        distribution_type="normal",
        parameters={"mean": 0.5, "stddev": 0.2},
    ),
    evolution_model=EvolutionModel(
        update_rule="conformity_update",
        deterministic=True,
        parameters={"local_influence": 0.7, "global_influence": 0.3},
    ),
    coupling_capacity={
        "max_runes": 3,
        "allowed_metric_classes": ["opinion_distribution", "peer_pressure"],
    },
    layer="world",
    provenance={"created": datetime.utcnow().isoformat() + "Z", "source": "exemplar"},
)

# --- WORLD LAYER: State-Over-Time (Temporal Correlation Container) ---
VAR_TEMPORAL_CORRELATION = SimVarDefinition(
    var_id="state_over_time_correlations",
    version="1.0.0",
    var_class="state_over_time",
    var_type="tensor",
    bounds={"shape": [10, 100, 100]},  # 10 timesteps, 100 features, covariance
    prior_distribution=PriorDistribution(
        distribution_type="custom",
        parameters={"correlation_prior": "identity"},  # No initial correlation
    ),
    evolution_model=EvolutionModel(
        update_rule="temporal_correlation",
        deterministic=True,
        parameters={"memory_length": 10, "decay_factor": 0.95},
    ),
    coupling_capacity={
        "max_runes": 2,
        "allowed_metric_classes": ["temporal_dynamics"],
    },
    layer="world",
    provenance={"created": datetime.utcnow().isoformat() + "Z", "source": "exemplar"},
)

# ==============================================================================
# ABX-RUNE BINDING (Quantum-Inspired / Hybrid)
# ==============================================================================

RUNE_MEDIA_COMPETITION = RuneBinding(
    rune_id="RUNE_MEDIA_COMPETITION_MISINFO",
    version="1.0.0",
    metric_id="MEDIA_COMPETITION_MISINFO_PRESSURE",
    var_targets=[
        VarTarget(var_id="public_opinion_belief_state", role="both"),
        VarTarget(var_id="media_framing_context", role="observe"),
        VarTarget(var_id="media_actor_credibility", role="observe"),
        VarTarget(var_id="misinformation_strategy_mix", role="both"),
        VarTarget(var_id="social_network_graph", role="observe"),
        VarTarget(var_id="community_assignment", role="observe"),
        VarTarget(var_id="conformity_pressure_field", role="observe"),
        VarTarget(var_id="state_over_time_correlations", role="influence"),
    ],
    layer_targets=["world", "media"],
    state_model="hybrid",  # Quantum-inspired + classical
    measurement_effect="partial-collapse",  # Observation affects belief state
    context_sensitivity=0.75,  # High context dependence
    observer_model=ObserverModel(
        observer_type="network_aggregate",
        parameters={
            "aggregation_function": "weighted_mean",
            "network_weights": "community_aware",
            "context_modulation": True,
        },
    ),
    transition_model=TransitionModel(
        transition_type="strategy_adapt",
        parameters={
            "payoff_function": "misinfo_reach_vs_credibility_cost",
            "nash_equilibrium_convergence": 0.1,
            "bounded_rationality": 0.2,  # Probabilistic strategy updates
        },
    ),
    noise_model=NoiseModel(
        noise_type="adversarial",
        parameters={
            "base_stddev": 0.05,
            "adversarial_boost": 2.0,  # Noise increases with manipulation
        },
    ),
    manipulation_model=ManipulationModel(
        manipulation_type="bot_amplification",
        penetration_scaling=1.5,  # Noise scales with bot penetration
        detection_threshold=0.6,  # Detected above 60% bot content
    ),
    constraints={
        "hard_bounds": {"enforce": True, "min": 0.0, "max": 1.0},
        "conservation_laws": [
            {"law_type": "probability", "tolerance": 1e-6},  # Belief probabilities sum to 1
        ],
    },
    provenance_manifest=ProvenanceManifest(
        created=datetime.utcnow().isoformat() + "Z",
        input_hash="a" * 64,  # Placeholder (would compute actual hash)
        metric_version="1.0.0",
        var_versions={
            "public_opinion_belief_state": "1.0.0",
            "media_framing_context": "1.0.0",
            "media_actor_credibility": "1.0.0",
            "misinformation_strategy_mix": "1.0.0",
            "social_network_graph": "1.0.0",
            "community_assignment": "1.0.0",
            "conformity_pressure_field": "1.0.0",
            "state_over_time_correlations": "1.0.0",
        },
        schema_version="1.0.0",
        sml_training_sources=["ARXIV_SPATIAL_GAMES", "PMC10924450"],
    ),
)

# ==============================================================================
# OUTCOME LEDGER ENTRY EXAMPLE
# ==============================================================================

OUTCOME_LEDGER_EXAMPLE = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "sim_seed": 42,
    "sim_version": "1.0.0",
    "active_metrics": [
        {"metric_id": "MEDIA_COMPETITION_MISINFO_PRESSURE", "version": "1.0.0"}
    ],
    "active_runes": [{"rune_id": "RUNE_MEDIA_COMPETITION_MISINFO", "version": "1.0.0"}],
    "prior_state_hash": "b" * 64,
    "prior_state_snapshot": {
        "public_opinion_mean": 0.1,
        "misinformation_strategy_mean": 0.2,
        "network_edges": 3000,
        "num_communities": 8,
    },
    "posterior_state_hash": "c" * 64,
    "posterior_state_snapshot": {
        "public_opinion_mean": 0.15,
        "misinformation_strategy_mean": 0.25,
        "network_edges": 3005,
        "num_communities": 8,
    },
    "predictions_issued": [
        {
            "prediction_id": "pred_001",
            "variable": "public_opinion_belief_state",
            "predicted_value": 0.18,
            "confidence_interval": {"lower": 0.12, "upper": 0.24, "level": 0.95},
            "horizon": 5,
        }
    ],
    "real_world_outcomes": [],
    "error_metrics": {"rmse": 0.03, "mae": 0.02},
    "confidence_deltas": {"MEDIA_COMPETITION_MISINFO_PRESSURE": -0.05},
    # --- CRITICAL DELTAS (Network + Game + Time) ---
    "measurement_disturbance": 0.08,  # Partial-collapse effect
    "world_media_divergence": 0.12,  # Divergence between world belief and media framing
    "network_drift": 0.015,  # 5 new edges / 3000 total ≈ 0.0017 (normalized)
    "strategy_shift": 0.05,  # L2 norm of strategy vector change
    "temporal_correlation_shift": 0.03,  # Change in correlation structure
    "community_stability": 0.95,  # 95% of nodes stayed in same community
    "conformity_pressure_avg": 0.52,  # Average conformity pressure
}

# ==============================================================================
# INTEGRATION WITH SML TRAINING DATA
# ==============================================================================

SML_INTEGRATION_NOTES = """
TRAINING DATA FLOW:

1. SML Paper Registry (data/sim_sources/papers.json):
   - ARXIV_SPATIAL_GAMES provides game-theoretic parameters (effort, sanction_prob, discount)

2. SML Parameter Mapping (abraxas/sim_mappings/):
   - map_paper_model() converts game-theoretic parameters to KnobVector
   - MRI from effort parameter → misinformation_strategy_mix prior
   - IRI from sanction_prob → media_actor_credibility prior
   - τ_memory from discount → state_over_time memory_length

3. SOD Adapter (abraxas/sod/sim_adapter.py):
   - convert_knobs_to_sod_priors() generates cascade_branching_prob, etc.
   - These priors inform prior_distribution parameters in SimVarDefinitions

4. Simulation Variable Initialization:
   - SimVarDefinition.prior_distribution.sml_source links back to paper_id
   - Provenance chain: Paper → KnobVector → SOD Priors → Variable Priors

5. Simulation Execution:
   - Runes use priors to initialize variables
   - Evolution models update state deterministically
   - Outcome ledger records provenance_manifest.sml_training_sources

EXAMPLE QUERY:
"What papers informed the misinformation_strategy_mix variable?"
Answer: ARXIV_SPATIAL_GAMES (see var prior sml_source)
"""
