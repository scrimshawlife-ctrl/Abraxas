from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.familiar.adapters.null_adapter import NullAdapter


class ERSAdapter:
    """
    Stub adapter that delegates to a deterministic null adapter by default.
    """

    def __init__(self, adapter: Optional[Any] = None) -> None:
        self._adapter = adapter or NullAdapter()

    def execute(self, run_plan: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        return self._adapter.execute(run_plan, inputs)
