"""
Ensemble Update Rules

Deterministic probability updates via eligible influences.
SSI-based integrity dampening. No ML, no randomness.
"""

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from abraxas.forecast.types import Branch, EnsembleState


class InfluenceEvent:
    """
    Simplified influence event for FBE updates.

    In full implementation, this would come from TER coupling.
    For v0.1, we use a simplified structure.
    """

    def __init__(
        self,
        influence_id: str,
        target: str,  # e.g., "MRI_push", "IRI_damp", "trust_surface_down"
        strength: float,  # 0.0-1.0
        source_type: str = "signal",  # "signal", "evidence_pack", "manual"
        provenance: Optional[Dict[str, Any]] = None,
    ):
        self.influence_id = influence_id
        self.target = target
        self.strength = strength
        self.source_type = source_type
        self.provenance = provenance or {}


def apply_influence_to_ensemble(
    ensemble: EnsembleState,
    influence_events: List[InfluenceEvent],
    integrity_snapshot: Optional[Dict[str, Any]] = None,
    now_ts: Optional[datetime] = None,
    max_delta_per_update: float = 0.15,
) -> EnsembleState:
    """
    Apply influence events to ensemble, updating branch probabilities.

    Deterministic update mechanics:
    1. For each influence, compute delta mass proposals per branch
    2. Dampen deltas by integrity (SSI-based)
    3. Apply bounded deltas
    4. Renormalize so sum(p) = 1.0
    5. Update confidence bands

    Args:
        ensemble: Current ensemble state
        influence_events: List of influences to apply
        integrity_snapshot: Optional integrity metrics (SSI, etc.)
        now_ts: Timestamp for update
        max_delta_per_update: Maximum absolute delta per branch per update

    Returns:
        Updated ensemble state
    """
    if now_ts is None:
        now_ts = datetime.now(timezone.utc)

    if integrity_snapshot is None:
        integrity_snapshot = {}

    # Work on a copy
    updated_ensemble = deepcopy(ensemble)

    # Track before probabilities for provenance
    probs_before = {b.branch_id: b.p for b in updated_ensemble.branches}

    # Process each influence
    for influence in influence_events:
        # Get branch-specific deltas for this influence
        branch_deltas = _compute_branch_deltas(
            influence, updated_ensemble.branches, integrity_snapshot, max_delta_per_update
        )

        # Apply deltas
        for branch in updated_ensemble.branches:
            delta = branch_deltas.get(branch.branch_id, 0.0)
            branch.p = max(0, min(1, branch.p + delta))

    # Renormalize to ensure sum(p) = 1.0
    total_p = sum(b.p for b in updated_ensemble.branches)
    if total_p > 0:
        for branch in updated_ensemble.branches:
            branch.p = branch.p / total_p

    # Update confidence bands based on evidence quality
    _update_confidence_bands(updated_ensemble.branches, integrity_snapshot)

    # Update timestamps and provenance
    updated_ensemble.last_updated_ts = now_ts
    for branch in updated_ensemble.branches:
        if abs(branch.p - probs_before[branch.branch_id]) > 0.001:
            branch.last_updated_at = now_ts

    # Add update provenance
    probs_after = {b.branch_id: b.p for b in updated_ensemble.branches}
    updated_ensemble.provenance = updated_ensemble.provenance or {}
    updated_ensemble.provenance["last_update"] = {
        "ts": now_ts.isoformat(),
        "influence_count": len(influence_events),
        "probs_before": probs_before,
        "probs_after": probs_after,
        "integrity_context": integrity_snapshot,
    }

    return updated_ensemble


def _compute_branch_deltas(
    influence: InfluenceEvent,
    branches: List[Branch],
    integrity_snapshot: Dict[str, Any],
    max_delta: float,
) -> Dict[str, float]:
    """
    Compute delta mass for each branch based on influence.

    Returns dict mapping branch_id to delta (can be positive or negative).
    """
    deltas = {}

    # Influence target to branch mapping (deterministic rules)
    influence_rules = _get_influence_rules()

    if influence.target not in influence_rules:
        # Unknown influence, no effect
        return {b.branch_id: 0.0 for b in branches}

    rule = influence_rules[influence.target]

    for branch in branches:
        if branch.label in rule.get("increases", []):
            # This branch gets positive delta
            delta_base = influence.strength * rule.get("strength_multiplier", 0.05)

            # Dampen by integrity if applicable
            delta = _apply_integrity_dampening(
                delta_base, branch, integrity_snapshot, influence.source_type
            )

            # Cap delta
            delta = max(-max_delta, min(max_delta, delta))

            deltas[branch.branch_id] = delta

        elif branch.label in rule.get("decreases", []):
            # This branch gets negative delta
            delta_base = -influence.strength * rule.get("strength_multiplier", 0.05)

            delta = _apply_integrity_dampening(
                delta_base, branch, integrity_snapshot, influence.source_type
            )

            delta = max(-max_delta, min(max_delta, delta))

            deltas[branch.branch_id] = delta

        else:
            # No effect on this branch
            deltas[branch.branch_id] = 0.0

    return deltas


def _get_influence_rules() -> Dict[str, Dict]:
    """
    Deterministic mapping from influence targets to branch effects.

    Returns dict mapping influence_target to:
    - increases: list of branch labels that increase
    - decreases: list of branch labels that decrease
    - strength_multiplier: how much influence strength affects delta
    """
    return {
        "MRI_push": {
            "increases": ["shock", "crisis", "collapsed"],
            "decreases": ["conservative"],
            "strength_multiplier": 0.08,
        },
        "IRI_damp": {
            "increases": ["conservative"],
            "decreases": ["shock", "crisis"],
            "strength_multiplier": 0.06,
        },
        "trust_surface_down": {
            "increases": ["degraded", "collapsed", "crisis"],
            "decreases": ["conservative"],
            "strength_multiplier": 0.10,
        },
        "tau_latency_up": {
            # Increases uncertainty across all branches (reduce deltas globally)
            "increases": [],
            "decreases": [],
            "strength_multiplier": -0.05,  # Negative = reduce all updates
        },
        "evidence_pack": {
            # Strong evidence supports specified branch (target determined by pack content)
            "increases": ["base", "sustained"],  # Default: moderate scenarios
            "decreases": [],
            "strength_multiplier": 0.12,
        },
    }


def _apply_integrity_dampening(
    delta_base: float,
    branch: Branch,
    integrity_snapshot: Dict[str, Any],
    source_type: str,
) -> float:
    """
    Dampen delta based on integrity (SSI) and branch sensitivity.

    Formula:
    damping_factor = 1 - (SSI * branch.manipulation_exposure.SSI_sensitivity)
    delta_actual = delta_base * damping_factor

    If source is evidence_pack, reduce dampening (trusted source).
    """
    # Evidence packs are trusted, minimal dampening
    if source_type == "evidence_pack":
        return delta_base

    # Get SSI from integrity snapshot
    ssi = integrity_snapshot.get("SSI", 0.5)
    ssi = max(0, min(1, ssi))  # Clamp to [0, 1]

    # Get branch SSI sensitivity
    sensitivity = branch.manipulation_exposure.get("SSI_sensitivity", 0.5)

    # Compute dampening factor
    dampening_factor = 1 - (ssi * sensitivity)
    dampening_factor = max(0, dampening_factor)  # Can't go negative

    # Apply dampening
    delta_actual = delta_base * dampening_factor

    return delta_actual


def _update_confidence_bands(
    branches: List[Branch], integrity_snapshot: Dict[str, Any]
):
    """
    Update p_min/p_max confidence bands based on evidence quality.

    More evidence + lower SSI = tighter bands.
    Less evidence + higher SSI = wider bands.
    """
    # Base band width
    base_band = 0.10

    # Adjust based on integrity
    ssi = integrity_snapshot.get("SSI", 0.5)
    completeness = integrity_snapshot.get("completeness", 0.7)

    # More SSI or less completeness = wider bands
    band_adjustment = (ssi * 0.5) + ((1 - completeness) * 0.3)
    band_width = base_band + band_adjustment

    # Cap band width
    band_width = min(0.25, band_width)

    for branch in branches:
        branch.p_min = max(0, branch.p - band_width)
        branch.p_max = min(1, branch.p + band_width)
