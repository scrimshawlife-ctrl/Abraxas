"""
ALIVE Metric Compute Function

Wrapper for the ALIVE engine that provides a standardized
interface for AAL-core function discovery and invocation.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from abraxas.alive.core import alive_run


def compute_alive(
    artifact: Dict[str, Any],
    tier: str = "psychonaut",
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compute ALIVE metric signature for an artifact.

    This is the standardized entrypoint for AAL-core integration.

    Args:
        artifact: Normalized artifact bundle (text/url/meta)
        tier: 'psychonaut' | 'academic' | 'enterprise'
        profile: Onboarding weights/traits (optional)

    Returns:
        AliveRunResult as dict (shape-correct, with full signature)
    """
    return alive_run(artifact=artifact, tier=tier, profile=profile)
