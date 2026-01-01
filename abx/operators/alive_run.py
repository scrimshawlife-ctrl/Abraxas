"""
ABX Operator: alive_run

Eurorack-style operator for running ALIVE analysis.
Can be chained with other Abraxas operators (ECO, slang, hyperstition, etc.).
"""

from __future__ import annotations

from typing import Any, Dict

from abraxas.alive import ALIVEEngine
from abraxas.alive.models import ALIVERunInput


class ALIVERunOperator:
    """
    ALIVE run operator.

    Executes ALIVE field signature analysis and returns results.
    """

    def __init__(self, registry_path: str | None = None):
        """
        Initialize ALIVE run operator.

        Args:
            registry_path: Path to metric registry
        """
        self.engine = ALIVEEngine(registry_path=registry_path)

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ALIVE analysis.

        Args:
            input_data: Analysis configuration

        Returns:
            Field signature as dict
        """
        # Parse input
        run_input = ALIVERunInput(**input_data)

        # Run engine
        field_signature = self.engine.run(run_input)

        # Return as dict
        return field_signature.model_dump()

    def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Allow operator to be called as function."""
        return self.execute(input_data)
