"""AAL (Abraxas Almanac Layer) - External overlay integrations.

This package contains rune adapters for external symbolic generation
and analysis overlays that integrate with Abraxas via ABX-Runes.

All external overlays:
- Must use capability contracts (no direct imports)
- Operate in OBSERVATION/GENERATION lane only
- Store results as artifacts with no_influence=True
- Follow incremental patch governance
"""

from abraxas.aal.artifact_handler import (
    NeonGenieArtifactHandler,
    store_neon_genie_result,
)
from abraxas.aal.neon_genie_adapter import generate_symbolic_v0

__all__ = [
    "generate_symbolic_v0",
    "NeonGenieArtifactHandler",
    "store_neon_genie_result",
]
