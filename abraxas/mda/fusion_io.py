from __future__ import annotations

from typing import Any, Dict

from .types import FusionGraph


def fusiongraph_from_json(obj: Dict[str, Any]) -> FusionGraph:
    # Minimal passthrough; callers treat this as an opaque structure.
    return obj or {"nodes": {}, "edges": []}

