"""
ABX Operator: alive_run

Eurorack-style operator for running ALIVE analysis.
Can be chained with other Abraxas operators (ECO, slang, hyperstition, etc.).
"""

from __future__ import annotations

from typing import Any, Dict

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


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
        self.registry_path = registry_path

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ALIVE analysis.

        Args:
            input_data: Analysis configuration

        Returns:
            Field signature as dict
        """
        run_id = str(input_data.get("subjectId") or input_data.get("analysisId") or "alive_run")
        ctx = RuneInvocationContext(
            run_id=run_id,
            subsystem_id="abx.operators.alive_run",
            git_hash="unknown",
        )
        result = invoke_capability(
            "alive.engine.run",
            {**input_data, "registry_path": self.registry_path},
            ctx=ctx,
            strict_execution=True,
        )
        return result["field_signature"]

    def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Allow operator to be called as function."""
        return self.execute(input_data)
