"""ABX-Rune Operator: ϟ₂ TAM

AUTO-GENERATED OPERATOR STUB
Rune: ϟ₂ TAM — Traversal-as-Meaning
Layer: Core
Motto: Meaning is the walk, not the map.

Canonical statement:
  Meaning emerges from path selection, not linear transmission.

Function:
  Treats meaning generation as emergent from path traversal rather than static transmission. Prioritizes dynamic interpretation over fixed semantics.

Inputs: traversal_path, node_sequence, context_history
Outputs: emergent_meaning, path_signature, semantic_trace

Constraints:
  - meaning_emerges_from_selection; no_predetermined_endpoints; path_dependent_interpretation

Provenance:
    - Star Gauge / Xuanji Tu traversal logic
  - Dynamic semantic graph theory
  - AAL traversal doctrine
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Iterable, Sequence

def _normalize_sequence(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    if isinstance(value, dict):
        return [str(v) for v in value.keys()]
    return [str(value)]


def _hash_sequence(values: Sequence[str]) -> str:
    payload = "|".join(values)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def apply_tam(
    traversal_path: Any,
    node_sequence: Any,
    context_history: Any,
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    """Apply TAM rune operator.

    Args:
                traversal_path: Input traversal_path
        node_sequence: Input node_sequence
        context_history: Input context_history
        strict_execution: If True, raises NotImplementedError for unimplemented operators

    Returns:
        Dict with keys: emergent_meaning, path_signature, semantic_trace

    Raises:
        NotImplementedError: If strict_execution=True and operator not implemented
    """
    missing = []
    if traversal_path is None:
        missing.append("traversal_path")
    if node_sequence is None:
        missing.append("node_sequence")
    if context_history is None:
        missing.append("context_history")
    if missing:
        if strict_execution:
            raise NotImplementedError(
                f"TAM requires inputs: {', '.join(missing)}"
            )
        return {
            "emergent_meaning": "",
            "path_signature": "",
            "semantic_trace": [],
            "not_computable": {
                "reason": "missing required inputs",
                "missing_inputs": missing,
            },
        }
    path_steps = _normalize_sequence(traversal_path)
    nodes = _normalize_sequence(node_sequence)
    history = _normalize_sequence(context_history)

    path_signature = _hash_sequence(path_steps or nodes)
    current_node = nodes[-1] if nodes else (path_steps[-1] if path_steps else "origin")
    history_hint = ", ".join(history[-3:]) if history else "no_context"
    emergent_meaning = f"{current_node} ⟶ {history_hint}"

    semantic_trace = [
        {
            "step": idx,
            "node": node,
            "context_hint": history[idx] if idx < len(history) else None,
        }
        for idx, node in enumerate(nodes or path_steps)
    ]

    return {
        "emergent_meaning": emergent_meaning,
        "path_signature": path_signature,
        "semantic_trace": semantic_trace,
    }
