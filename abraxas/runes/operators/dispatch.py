"""Dynamic ABX-Rune operator dispatcher.

Provides runtime resolution of rune IDs to operator functions.
"""

from __future__ import annotations
from typing import Any, Dict

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_rune

def dispatch(rune_id: str, *, ctx: RuneInvocationContext | dict, **kwargs: Any) -> Dict[str, Any]:
    """Dynamic ABX-Rune dispatcher.

    Resolves rune_id -> definition -> operator module apply_<short_name>.
    If the operator is missing, raises a clear error.

    Args:
        rune_id: Rune identifier (e.g., "ϟ₁", "ϟ₂")
        **kwargs: Arguments to pass to the operator function
        ctx: Required rune invocation context

    Returns:
        Dict containing operator outputs

    Raises:
        RuneInvocationError: If rune invocation fails

    Example:
        >>> result = dispatch("ϟ₁", ctx=ctx, semantic_field=data, context_vector=ctx)
    """
    return invoke_rune(rune_id, kwargs, ctx=ctx)
