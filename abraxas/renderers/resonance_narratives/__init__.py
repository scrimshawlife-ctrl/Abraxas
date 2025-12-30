"""
Resonance Narratives Renderer v1

Converts Oracle v2 envelopes into human-readable narrative bundles
with full pointer-based auditability.

Philosophy:
- No invention: every statement maps to envelope fields
- Evidence gating: no claims without evidence
- Deterministic: same envelope → same narrative
- Diff-friendly: structured output, not prose
"""

from abraxas.renderers.resonance_narratives.renderer import (
    render_narrative_bundle,
    render_narrative_bundle_with_diff,
)

__all__ = [
    "render_narrative_bundle",
    "render_narrative_bundle_with_diff",
]
