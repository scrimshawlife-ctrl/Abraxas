"""Event Correlation (v0.1).

Offline-first, deterministic correlator that emits pointer-auditable evidence refs.
"""

from .correlator import CorrelatorConfig, correlate

__all__ = ["CorrelatorConfig", "correlate"]

