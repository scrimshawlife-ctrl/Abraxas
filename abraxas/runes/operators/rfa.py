"""ABX-Rune Operator: ϟ₁ RFA

AUTO-GENERATED OPERATOR STUB
Rune: ϟ₁ RFA — Resonant Field Anchor
Layer: Core
Motto: Stabilize meaning by fixing the center, not the path.

Canonical statement:
  Stabilize meaning by fixing the center, not the path.

Function:
  Establishes a stable semantic anchor point that allows meaning to resonate without requiring rigid pathway control. Enables drift-tolerant interpretation.

Inputs: semantic_field, context_vector, anchor_candidates
Outputs: anchored_field, resonance_strength, stability_metric

Constraints:
  - anchor_must_remain_invariant; resonance_bounded_by_field_radius; no_forced_path_constraints

Provenance:
    - Star Gauge / Xuanji Tu traversal logic
  - Schumann resonance physics corpus
  - AAL semantic anchor doctrine
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Iterable, Sequence

def _tokenize(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v).lower() for v in value]
    if isinstance(value, dict):
        return [str(v).lower() for v in value.keys()]
    return str(value).lower().split()


def _score_anchor(anchor: str, field_tokens: Sequence[str], context_tokens: Sequence[str]) -> float:
    anchor_tokens = set(_tokenize(anchor))
    if not anchor_tokens:
        return 0.0
    field_overlap = len(anchor_tokens & set(field_tokens)) / len(anchor_tokens)
    context_overlap = len(anchor_tokens & set(context_tokens)) / len(anchor_tokens)
    return 0.7 * field_overlap + 0.3 * context_overlap


def apply_rfa(
    semantic_field: Any,
    context_vector: Any,
    anchor_candidates: Any,
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    """Apply RFA rune operator.

    Args:
                semantic_field: Input semantic_field
        context_vector: Input context_vector
        anchor_candidates: Input anchor_candidates
        strict_execution: If True, raises NotImplementedError for unimplemented operators

    Returns:
        Dict with keys: anchored_field, resonance_strength, stability_metric

    Raises:
        NotImplementedError: If strict_execution=True and operator not implemented
    """
    missing = []
    if semantic_field is None:
        missing.append("semantic_field")
    if context_vector is None:
        missing.append("context_vector")
    if anchor_candidates is None:
        missing.append("anchor_candidates")
    if missing:
        if strict_execution:
            raise NotImplementedError(
                f"RFA requires inputs: {', '.join(missing)}"
            )
        return {
            "anchored_field": {},
            "resonance_strength": 0.0,
            "stability_metric": 0.0,
            "not_computable": {
                "reason": "missing required inputs",
                "missing_inputs": missing,
            },
        }
    field_tokens = _tokenize(semantic_field)
    context_tokens = _tokenize(context_vector)

    candidates: list[str]
    if isinstance(anchor_candidates, (list, tuple, set)):
        candidates = [str(c) for c in anchor_candidates if str(c).strip()]
    elif isinstance(anchor_candidates, dict):
        candidates = [str(c) for c in anchor_candidates.keys()]
    elif anchor_candidates is None:
        candidates = []
    else:
        candidates = [str(anchor_candidates)]

    if not candidates:
        fallback = " ".join(field_tokens[:6]) if field_tokens else "anchor.undefined"
        anchor = fallback
        resonance_strength = 0.0
        stability_metric = 0.0
    else:
        scores = {c: _score_anchor(c, field_tokens, context_tokens) for c in candidates}
        anchor = max(scores, key=scores.get)
        resonance_strength = scores[anchor]
        score_values = list(scores.values())
        stability_metric = 1.0 - (max(score_values) - min(score_values)) if score_values else 0.0
        stability_metric = max(0.0, min(1.0, stability_metric))

    anchored_field = {
        "anchor": anchor,
        "field_tokens": field_tokens,
        "context_tokens": context_tokens,
        "anchor_hash": hashlib.sha256(anchor.encode("utf-8")).hexdigest(),
    }

    return {
        "anchored_field": anchored_field,
        "resonance_strength": round(resonance_strength, 6),
        "stability_metric": round(stability_metric, 6),
    }
