"""Phase Management

Manages phases in overlay operations.
"""

from enum import Enum
from typing import List, Optional


class Phase(Enum):
    """Enumeration of overlay phases."""
    INIT = "init"
    PROCESS = "process"
    TRANSFORM = "transform"
    FINALIZE = "finalize"


class PhaseManager:
    """Manages phase transitions and execution."""

    def __init__(self):
        """Initialize the phase manager."""
        self.current_phase: Optional[Phase] = None
        self.phase_history: List[Phase] = []
        self.handlers = {}

    def register_handler(self, phase: Phase, handler_fn):
        """Register a handler for a specific phase.

        Args:
            phase: The phase to handle
            handler_fn: Function to execute during this phase
        """
        self.handlers[phase] = handler_fn

    def transition(self, phase: Phase):
        """Transition to a new phase.

        Args:
            phase: The phase to transition to
        """
        if self.current_phase:
            self.phase_history.append(self.current_phase)
        self.current_phase = phase

    def execute(self, phase: Phase, *args, **kwargs):
        """Execute a phase handler.

        Args:
            phase: The phase to execute
            *args: Positional arguments for the handler
            **kwargs: Keyword arguments for the handler

        Returns:
            Result of the phase handler
        """
        if phase not in self.handlers:
            raise ValueError(f"No handler registered for phase '{phase.value}'")

        self.transition(phase)
        return self.handlers[phase](*args, **kwargs)
