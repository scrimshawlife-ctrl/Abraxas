"""Dynamic ABX-Rune operator dispatcher.

Provides runtime resolution of rune IDs to operator functions.
"""

from __future__ import annotations
from typing import Any, Dict, Callable
import importlib
from pathlib import Path
import json

def _runes_root() -> Path:
    return Path(__file__).resolve().parents[1]

def _load_defs() -> list[dict]:
    defs_dir = _runes_root() / "definitions"
    out = []
    for p in sorted(defs_dir.glob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out

def dispatch(rune_id: str, **kwargs: Any) -> Dict[str, Any]:
    """Dynamic ABX-Rune dispatcher.

    Resolves rune_id -> definition -> operator module apply_<short_name>.
    If the operator is missing, raises a clear error.

    Args:
        rune_id: Rune identifier (e.g., "ϟ₁", "ϟ₂")
        **kwargs: Arguments to pass to the operator function

    Returns:
        Dict containing operator outputs

    Raises:
        KeyError: If rune_id is unknown
        ImportError: If operator module is missing
        AttributeError: If operator function is missing

    Example:
        >>> result = dispatch("ϟ₁", semantic_field=data, context_vector=ctx)
    """
    defs = _load_defs()
    match = None
    for d in defs:
        if d.get("id") == rune_id:
            match = d
            break
    if not match:
        raise KeyError(f"Unknown rune id: {rune_id}")

    short_name = str(match["short_name"]).strip().lower()
    mod_name = short_name
    fn_name = f"apply_{short_name}"

    try:
        mod = importlib.import_module(f"abraxas.runes.operators.{mod_name}")
    except Exception as e:
        raise ImportError(
            f"Missing operator module for rune {rune_id} ({match['short_name']}): "
            f"abraxas.runes.operators.{mod_name}"
        ) from e

    fn = getattr(mod, fn_name, None)
    if not callable(fn):
        raise AttributeError(
            f"Missing operator function {fn_name} in module "
            f"abraxas.runes.operators.{mod_name}"
        )

    return fn(**kwargs)
