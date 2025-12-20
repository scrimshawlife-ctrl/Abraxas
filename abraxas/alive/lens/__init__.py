"""
ALIVE lens translators — tier-specific view transformations.

Each lens translates raw ALIVE signature into tier-appropriate outputs:
- psychonaut: felt-state (pressure/pull/agency/drift)
- academic: full transparency + operational definitions
- enterprise: production metrics + business risk
"""

from abraxas.alive.lens.psychonaut import psychonaut_translate

__all__ = ["psychonaut_translate"]
