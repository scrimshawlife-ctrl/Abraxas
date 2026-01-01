"""OAS Stabilizer: ensures candidates are stable across multiple validation cycles."""

from __future__ import annotations

from datetime import datetime, timezone

from abraxas.oasis.models import OperatorCandidate, StabilizationState, ValidationReport


class OASStabilizer:
    """
    Manages stabilization of operator candidates.

    Requires N cycles of consistent improvement before canonization.
    """

    def __init__(self, cycles_required: int = 3, consistency_threshold: float = 0.8):
        """
        Initialize stabilizer.

        Args:
            cycles_required: Number of validation cycles required
            consistency_threshold: Proportion of cycles that must pass
        """
        self.cycles_required = cycles_required
        self.consistency_threshold = consistency_threshold
        self.states: dict[str, StabilizationState] = {}

    def check_stability(
        self, candidate: OperatorCandidate, reports: list[ValidationReport]
    ) -> StabilizationState:
        """
        Check stability of a candidate given validation reports.

        Returns updated StabilizationState.
        """
        operator_id = candidate.operator_id

        # Get or create state
        if operator_id not in self.states:
            self.states[operator_id] = StabilizationState(
                operator_id=operator_id,
                cycles_required=self.cycles_required,
                cycles_completed=0,
                last_reports=[],
                stable=False,
            )

        state = self.states[operator_id]

        # Add new reports
        state.last_reports.extend(reports)

        # Keep only most recent cycles
        state.last_reports = state.last_reports[-self.cycles_required :]

        # Update cycles completed
        state.cycles_completed = len(state.last_reports)

        # Check if stable
        if state.cycles_completed >= self.cycles_required:
            passed_count = sum(1 for r in state.last_reports if r.passed)
            consistency = passed_count / state.cycles_completed

            if consistency >= self.consistency_threshold:
                state.stable = True
                state.completed_at = datetime.now(timezone.utc)
                state.notes.append(
                    f"Stable: {passed_count}/{state.cycles_completed} cycles passed"
                )
            else:
                state.stable = False
                state.notes.append(
                    f"Unstable: {passed_count}/{state.cycles_completed} cycles passed "
                    f"(threshold: {self.consistency_threshold})"
                )
        else:
            state.stable = False
            state.notes.append(
                f"Insufficient cycles: {state.cycles_completed}/{self.cycles_required}"
            )

        return state

    def get_state(self, operator_id: str) -> StabilizationState | None:
        """Get stabilization state for an operator."""
        return self.states.get(operator_id)

    def reset_state(self, operator_id: str) -> None:
        """Reset stabilization state for an operator."""
        if operator_id in self.states:
            del self.states[operator_id]
