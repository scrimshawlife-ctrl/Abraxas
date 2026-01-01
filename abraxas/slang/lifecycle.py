"""Slang Lifecycle State Machine.

Defines the lifecycle states for symbolic evolution and deterministic
transition rules based on τ (tau) metrics and recurrence counts.

States: Proto → Front → Saturated → Dormant → Archived
Revival requires mutation evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from abraxas.core.temporal_tau import TauSnapshot


class LifecycleState(str, Enum):
    """Canonical lifecycle states for symbolic evolution."""

    PROTO = "Proto"  # Initial emergence
    FRONT = "Front"  # Active spread
    SATURATED = "Saturated"  # Peak adoption
    DORMANT = "Dormant"  # Declining use
    ARCHIVED = "Archived"  # Obsolete


@dataclass(frozen=True)
class TransitionThresholds:
    """Thresholds for lifecycle state transitions."""

    # Proto → Front
    proto_to_front_velocity: float = 0.5  # τᵥ threshold
    proto_to_front_min_obs: int = 5

    # Front → Saturated
    front_to_saturated_velocity_max: float = 0.1  # |τᵥ| < threshold
    front_to_saturated_half_life_min: float = 168.0  # τₕ > 7 days

    # Saturated → Dormant
    saturated_to_dormant_velocity: float = -0.1  # τᵥ < threshold

    # Dormant → Archived
    dormant_to_archived_half_life_max: float = 24.0  # τₕ < 1 day

    # Revival (any → Proto)
    revival_min_edit_distance: int = 2


@dataclass(frozen=True)
class MutationEvidence:
    """Evidence of symbolic mutation for revival detection."""

    edit_distance: int
    token_modifier_changed: bool
    description: str


class LifecycleEngine:
    """
    Deterministic lifecycle state machine.

    Computes state transitions based on τ snapshots and mutation evidence.
    """

    def __init__(self, thresholds: Optional[TransitionThresholds] = None):
        """Initialize engine with optional custom thresholds."""
        self.thresholds = thresholds or TransitionThresholds()

    def compute_state(
        self,
        current_state: LifecycleState,
        tau_snapshot: TauSnapshot,
        mutation_evidence: Optional[MutationEvidence] = None,
    ) -> LifecycleState:
        """
        Compute next lifecycle state based on current state and τ snapshot.

        Args:
            current_state: Current lifecycle state
            tau_snapshot: τ metrics snapshot
            mutation_evidence: Optional mutation evidence for revival

        Returns:
            Next lifecycle state (may be same as current)
        """
        # Check for revival first (can happen from any state)
        if mutation_evidence and self._is_revival(mutation_evidence, tau_snapshot):
            return LifecycleState.PROTO

        # State-specific transitions
        if current_state == LifecycleState.PROTO:
            return self._transition_from_proto(tau_snapshot)
        elif current_state == LifecycleState.FRONT:
            return self._transition_from_front(tau_snapshot)
        elif current_state == LifecycleState.SATURATED:
            return self._transition_from_saturated(tau_snapshot)
        elif current_state == LifecycleState.DORMANT:
            return self._transition_from_dormant(tau_snapshot)
        elif current_state == LifecycleState.ARCHIVED:
            # Archived only transitions via revival
            return current_state
        else:
            return current_state

    def _transition_from_proto(self, tau: TauSnapshot) -> LifecycleState:
        """Proto → Front transition check."""
        if (
            tau.tau_velocity > self.thresholds.proto_to_front_velocity
            and tau.observation_count >= self.thresholds.proto_to_front_min_obs
        ):
            return LifecycleState.FRONT
        return LifecycleState.PROTO

    def _transition_from_front(self, tau: TauSnapshot) -> LifecycleState:
        """Front → Saturated transition check."""
        if (
            abs(tau.tau_velocity) < self.thresholds.front_to_saturated_velocity_max
            and tau.tau_half_life > self.thresholds.front_to_saturated_half_life_min
        ):
            return LifecycleState.SATURATED
        return LifecycleState.FRONT

    def _transition_from_saturated(self, tau: TauSnapshot) -> LifecycleState:
        """Saturated → Dormant transition check."""
        if tau.tau_velocity < self.thresholds.saturated_to_dormant_velocity:
            return LifecycleState.DORMANT
        return LifecycleState.SATURATED

    def _transition_from_dormant(self, tau: TauSnapshot) -> LifecycleState:
        """Dormant → Archived transition check."""
        if tau.tau_half_life < self.thresholds.dormant_to_archived_half_life_max:
            return LifecycleState.ARCHIVED
        return LifecycleState.DORMANT

    def _is_revival(
        self, mutation_evidence: MutationEvidence, tau: TauSnapshot
    ) -> bool:
        """
        Check if mutation evidence + new observations indicate revival.

        Args:
            mutation_evidence: Mutation evidence
            tau: τ snapshot (must have recent observations)

        Returns:
            True if revival conditions met
        """
        # Revival requires significant mutation AND recent observation
        has_mutation = (
            mutation_evidence.edit_distance >= self.thresholds.revival_min_edit_distance
            or mutation_evidence.token_modifier_changed
        )
        has_recent_obs = tau.observation_count > 0 and tau.tau_velocity > 0

        return has_mutation and has_recent_obs


def compute_edit_distance(term1: str, term2: str) -> int:
    """
    Compute Levenshtein edit distance between two terms.

    Deterministic string distance metric for mutation detection.

    Args:
        term1: First term
        term2: Second term

    Returns:
        Edit distance (number of single-character edits)
    """
    # Classic dynamic programming Levenshtein distance
    if term1 == term2:
        return 0

    len1, len2 = len(term1), len(term2)
    if len1 == 0:
        return len2
    if len2 == 0:
        return len1

    # Create distance matrix
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    # Initialize first row and column
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j

    # Fill matrix
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if term1[i - 1] == term2[j - 1]:
                cost = 0
            else:
                cost = 1

            matrix[i][j] = min(
                matrix[i - 1][j] + 1,  # deletion
                matrix[i][j - 1] + 1,  # insertion
                matrix[i - 1][j - 1] + cost,  # substitution
            )

    return matrix[len1][len2]
