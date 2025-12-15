"""Phase Management

Overlay phase dispatcher that routes phase execution to the kernel.
Maintains backward compatibility with legacy PhaseManager.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from .schema import Phase
from abraxas.kernel.entry import run_phase


def dispatch(phase: Phase, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a phase execution request to the kernel.

    Args:
        phase: The phase to execute (OPEN, ALIGN, ASCEND, CLEAR, SEAL)
        payload: Input data for the phase

    Returns:
        Result dictionary from the kernel phase execution
    """
    return run_phase(phase, payload)


# Legacy PhaseManager for backward compatibility with OverlayRunner
class LegacyPhase(Enum):
    """Legacy enumeration of overlay phases."""
    INIT = "init"
    PROCESS = "process"
    TRANSFORM = "transform"
    FINALIZE = "finalize"


class PhaseManager:
    """Legacy phase manager for backward compatibility.

    Note: New code should use the dispatch() function with kernel phases.
    """

    def __init__(self):
        """Initialize the phase manager."""
        self.current_phase: Optional[LegacyPhase] = None
        self.phase_history: List[LegacyPhase] = []
        self.handlers = {}

    def register_handler(self, phase: LegacyPhase, handler_fn):
        """Register a handler for a specific phase.

        Args:
            phase: The phase to handle
            handler_fn: Function to execute during this phase
        """
        self.handlers[phase] = handler_fn

    def transition(self, phase: LegacyPhase):
        """Transition to a new phase.

        Args:
            phase: The phase to transition to
        """
        if self.current_phase:
            self.phase_history.append(self.current_phase)
        self.current_phase = phase

    def execute(self, phase: LegacyPhase, *args, **kwargs):
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
