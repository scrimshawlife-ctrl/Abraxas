"""
MDA (Metric/Domain Analysis) shim layer used by oracle batch tooling.

This package is intentionally small and deterministic. It provides:
- Stable JSON hashing utilities (via core canonical helpers)
- A minimal "oracle_signal_v2" envelope used for batch practice runs
"""

from .types import sha256_hex, stable_json_dumps

__all__ = ["sha256_hex", "stable_json_dumps"]

