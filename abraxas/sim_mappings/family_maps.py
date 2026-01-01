"""SML Family Maps: Family-specific parameter mapping rules.

Defines key parameters and mapping rules for each ModelFamily:
- DIFFUSION_SIR
- OPINION_DYNAMICS
- ABM_MISINFO
- NETWORK_CASCADES
- GAME_THEORETIC

Each family has:
- Key params list (for evidence completeness)
- MRI contributors (push/spread/amplification)
- IRI contributors (damping/redirect/defense)
- τ contributors (timing/memory)
"""

from __future__ import annotations

from typing import Dict, List

from abraxas.sim_mappings.types import ModelFamily

# ============================================================================
# KEY PARAMETERS PER FAMILY (for evidence completeness scoring)
# ============================================================================

FAMILY_KEY_PARAMS: Dict[ModelFamily, List[str]] = {
    ModelFamily.DIFFUSION_SIR: [
        "beta",  # Transmission rate
        "gamma",  # Recovery rate
        "k",  # Network degree
        "delay",  # Incubation/exposure delay
    ],
    ModelFamily.OPINION_DYNAMICS: [
        "w",  # Influence weight
        "epsilon",  # Bounded confidence
        "alpha",  # Inertia/relaxation
        "update_schedule",  # Update timing
    ],
    ModelFamily.ABM_MISINFO: [
        "share_prob",  # Sharing probability
        "bot_density",  # Bot proportion
        "correction_eff",  # Correction effectiveness
        "content_lifespan",  # Content memory
    ],
    ModelFamily.NETWORK_CASCADES: [
        "p",  # Activation probability
        "threshold",  # Adoption threshold
        "deactivation_rate",  # Recovery rate
        "delay",  # Propagation delay
    ],
    ModelFamily.GAME_THEORETIC: [
        "effort",  # Propagandist effort
        "sanction_prob",  # Sanction probability
        "sanction_penalty",  # Sanction cost
        "discount",  # Discount factor
    ],
}


# ============================================================================
# PARAMETER ROLE ASSIGNMENTS (which knob does each param contribute to?)
# ============================================================================

# DIFFUSION_SIR mapping
DIFFUSION_SIR_MRI_PARAMS = [
    "beta",  # Transmission rate (higher = more spread)
    "c2",  # External boost/advertising
    "ads",  # Media influence
    "k",  # Network degree (higher = more contacts)
    "mixing",  # Mixing parameter (higher = less structure)
]

DIFFUSION_SIR_IRI_PARAMS = [
    "gamma",  # Recovery/forgetting rate (higher = faster recovery)
    "skeptic_rate",  # Skeptic compartment transition
    "immune_rate",  # Immune compartment transition
    "defensive_mod",  # Defensive modifiers reducing beta
]

DIFFUSION_SIR_TAU_PARAMS = [
    "delay",  # Incubation/exposure delay
    "incubation",  # Alternate name for delay
    "inter_layer_lag",  # Multi-layer model lag
    "memory_kernel",  # Non-Markovian memory
]

# OPINION_DYNAMICS mapping
OPINION_DYNAMICS_MRI_PARAMS = [
    "w",  # Influence weight (higher = stronger influence)
    "w_ij",  # Pairwise influence
    "homophily",  # Homophily parameter (higher = echo chambers)
    "media_field",  # Mass media field strength
]

OPINION_DYNAMICS_IRI_PARAMS = [
    "epsilon",  # Bounded confidence (lower = more selective)
    "stubbornness",  # Zealot/stubborn parameter
    "repulsion",  # Negative influence
    "bounded_conf",  # Alternate name for epsilon
]

OPINION_DYNAMICS_TAU_PARAMS = [
    "update_schedule",  # Update timing parameter
    "alpha",  # Inertia/relaxation (lower = faster updates)
    "memory_depth",  # Argument memory depth
    "inertia",  # Alternate name for alpha
]

# ABM_MISINFO mapping
ABM_MISINFO_MRI_PARAMS = [
    "share_prob",  # Sharing probability
    "bot_density",  # Bot density
    "bot_activity",  # Bot activity rate
    "algo_boost",  # Algorithmic amplification
]

ABM_MISINFO_IRI_PARAMS = [
    "correction_eff",  # Correction effectiveness
    "sanction",  # Sanction parameter
    "downrank",  # Downranking parameter
    "trust_adaptive",  # Adaptive trust dynamics
]

ABM_MISINFO_TAU_PARAMS = [
    "inter_event_time",  # Time between events
    "exposure_action_delay",  # Delay between exposure and action
    "content_lifespan",  # Content memory/lifespan
]

# NETWORK_CASCADES mapping
NETWORK_CASCADES_MRI_PARAMS = [
    "p",  # Edge activation probability
    "p_ij",  # Pairwise activation
    "threshold",  # Adoption threshold (INVERTED: lower = higher MRI)
    "bridge_density",  # Bridge density
]

NETWORK_CASCADES_IRI_PARAMS = [
    "deactivation_rate",  # Deactivation/recovery rate
    "robustness",  # Network robustness
    "redundancy",  # Redundancy parameter
    "moderation_removal",  # Moderation removal rate
]

NETWORK_CASCADES_TAU_PARAMS = [
    "delay",  # Propagation delay
    "temporal_window",  # Temporal window parameter
    "propagation_delay",  # Alternate name for delay
]

# GAME_THEORETIC mapping
GAME_THEORETIC_MRI_PARAMS = [
    "effort",  # Propagandist effort/investment
    "payoff_reach",  # Payoff reach incentive
    "selection_strength",  # Selection strength (higher = faster spread)
]

GAME_THEORETIC_IRI_PARAMS = [
    "sanction_prob",  # Sanction probability p_C
    "sanction_penalty",  # Sanction penalty cost
    "defender_budget",  # Defender budget
]

GAME_THEORETIC_TAU_PARAMS = [
    "update_schedule",  # Update schedule parameter
    "observation_horizon",  # Observation horizon
    "discount",  # Discount factor (lower = shorter horizon)
    "campaign_horizon",  # Campaign time horizon
]


# ============================================================================
# NORMALIZATION RANGES (conservative defaults for common parameters)
# ============================================================================

# Default ranges for common parameters (used if paper doesn't specify)
DEFAULT_PARAM_RANGES: Dict[str, tuple[float, float]] = {
    # DIFFUSION_SIR
    "beta": (0.0, 1.0),  # Transmission rate per contact
    "gamma": (0.0, 1.0),  # Recovery rate
    "k": (1.0, 50.0),  # Network degree
    "delay": (0.0, 14.0),  # Days
    # OPINION_DYNAMICS
    "w": (0.0, 1.0),  # Influence weight
    "epsilon": (0.0, 1.0),  # Bounded confidence
    "alpha": (0.0, 1.0),  # Inertia
    # ABM_MISINFO
    "share_prob": (0.0, 1.0),  # Probability
    "bot_density": (0.0, 0.5),  # Fraction of bots
    "correction_eff": (0.0, 1.0),  # Effectiveness
    # NETWORK_CASCADES
    "p": (0.0, 1.0),  # Activation probability
    "threshold": (0.0, 1.0),  # Adoption threshold
    "deactivation_rate": (0.0, 1.0),  # Rate
    # GAME_THEORETIC
    "effort": (0.0, 10.0),  # Effort units
    "sanction_prob": (0.0, 1.0),  # Probability
    "discount": (0.0, 1.0),  # Discount factor
    # Common temporal params
    "inter_event_time": (0.0, 24.0),  # Hours
    "content_lifespan": (0.0, 168.0),  # Hours (1 week max)
}


def get_family_key_params(family: ModelFamily) -> List[str]:
    """Get key parameter names for a model family."""
    return FAMILY_KEY_PARAMS.get(family, [])


def get_mri_params(family: ModelFamily) -> List[str]:
    """Get MRI contributor parameter names for a model family."""
    mapping = {
        ModelFamily.DIFFUSION_SIR: DIFFUSION_SIR_MRI_PARAMS,
        ModelFamily.OPINION_DYNAMICS: OPINION_DYNAMICS_MRI_PARAMS,
        ModelFamily.ABM_MISINFO: ABM_MISINFO_MRI_PARAMS,
        ModelFamily.NETWORK_CASCADES: NETWORK_CASCADES_MRI_PARAMS,
        ModelFamily.GAME_THEORETIC: GAME_THEORETIC_MRI_PARAMS,
    }
    return mapping.get(family, [])


def get_iri_params(family: ModelFamily) -> List[str]:
    """Get IRI contributor parameter names for a model family."""
    mapping = {
        ModelFamily.DIFFUSION_SIR: DIFFUSION_SIR_IRI_PARAMS,
        ModelFamily.OPINION_DYNAMICS: OPINION_DYNAMICS_IRI_PARAMS,
        ModelFamily.ABM_MISINFO: ABM_MISINFO_IRI_PARAMS,
        ModelFamily.NETWORK_CASCADES: NETWORK_CASCADES_IRI_PARAMS,
        ModelFamily.GAME_THEORETIC: GAME_THEORETIC_IRI_PARAMS,
    }
    return mapping.get(family, [])


def get_tau_params(family: ModelFamily) -> List[str]:
    """Get τ contributor parameter names for a model family."""
    mapping = {
        ModelFamily.DIFFUSION_SIR: DIFFUSION_SIR_TAU_PARAMS,
        ModelFamily.OPINION_DYNAMICS: OPINION_DYNAMICS_TAU_PARAMS,
        ModelFamily.ABM_MISINFO: ABM_MISINFO_TAU_PARAMS,
        ModelFamily.NETWORK_CASCADES: NETWORK_CASCADES_TAU_PARAMS,
        ModelFamily.GAME_THEORETIC: GAME_THEORETIC_TAU_PARAMS,
    }
    return mapping.get(family, [])


def get_param_range(param_name: str) -> tuple[float, float]:
    """Get default normalization range for a parameter."""
    return DEFAULT_PARAM_RANGES.get(param_name, (0.0, 1.0))


def is_inverted_param(param_name: str) -> bool:
    """Check if parameter has inverted semantics (lower value = higher risk)."""
    # Threshold is inverted: lower threshold = easier to activate = higher MRI
    inverted_params = {"threshold", "epsilon", "bounded_conf", "discount"}
    return param_name in inverted_params
