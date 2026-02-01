"""
ABX Operator: alive_run

Eurorack-style operator for running ALIVE analysis.
Can be chained with other Abraxas operators (ECO, slang, hyperstition, etc.).
"""

from __future__ import annotations

from typing import Any, Dict

# ALIVEEngine and ALIVERunInput replaced by alive.run capability
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


class ALIVERunOperator:
    """
    ALIVE run operator.

    Executes ALIVE field signature analysis and returns results.
    """

    def __init__(self, registry_path: str | None = None):
        """
        Initialize ALIVE run operator.

        Args:
            registry_path: Path to metric registry (unused with capability)
        """
        # Registry path is unused with capability-based invocation
        self.registry_path = registry_path

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ALIVE analysis.

        Args:
            input_data: Analysis configuration with artifact, tier, profile

        Returns:
            Field signature as dict
        """
        # Extract parameters
        artifact = input_data.get("artifact", {})
        tier = input_data.get("tier", "psychonaut")
        profile = input_data.get("profile")

        # Create invocation context
        ctx = RuneInvocationContext(
            run_id=input_data.get("run_id", "ALIVE_RUN"),
            subsystem_id="abx.operators.alive_run",
            git_hash="unknown"
        )

        # Invoke ALIVE capability
        result = invoke_capability(
            "alive.run",
            {
                "artifact": artifact,
                "tier": tier,
                "profile": profile
            },
            ctx=ctx,
            strict_execution=True
        )

        # Return the analysis result
        return result["result"]

    def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Allow operator to be called as function."""
        return self.execute(input_data)
