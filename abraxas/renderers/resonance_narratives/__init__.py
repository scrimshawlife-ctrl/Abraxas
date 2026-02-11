"""
Resonance Narratives renderer (v0.1, renderer-only).
"""

from typing import Any, Dict, Optional

from .renderer import NarrativeError, RenderConfig, render
from .rules import NarrativeRules, default_rules


def _ensure_artifact_id(envelope: Dict[str, Any], artifact_id: Optional[str]) -> Dict[str, Any]:
    """Ensure envelope has an artifact_id, injecting one if needed."""
    id_keys = ("artifact_id", "id", "artifactId", "run_id")
    if any(envelope.get(k) for k in id_keys):
        if artifact_id:
            return {**envelope, "artifact_id": artifact_id}
        return envelope
    return {**envelope, "artifact_id": artifact_id or "auto-generated"}


def render_narrative_bundle(
    envelope: Dict[str, Any],
    *,
    artifact_id: Optional[str] = None,
    rules: Optional[NarrativeRules] = None,
    cfg: Optional[RenderConfig] = None,
) -> Dict[str, Any]:
    """Convenience wrapper: render a single envelope into a narrative bundle."""
    envelope = _ensure_artifact_id(envelope, artifact_id)
    return render(envelope, rules=rules, cfg=cfg)


def render_narrative_bundle_with_diff(
    envelope: Dict[str, Any],
    *,
    previous_envelope: Optional[Dict[str, Any]] = None,
    artifact_id: Optional[str] = None,
    rules: Optional[NarrativeRules] = None,
    cfg: Optional[RenderConfig] = None,
) -> Dict[str, Any]:
    """Convenience wrapper: render with diff against a previous envelope."""
    envelope = _ensure_artifact_id(envelope, artifact_id)
    return render(envelope, previous_envelope_v2=previous_envelope, rules=rules, cfg=cfg)


__all__ = [
    "NarrativeError",
    "NarrativeRules",
    "RenderConfig",
    "default_rules",
    "render",
    "render_narrative_bundle",
    "render_narrative_bundle_with_diff",
]
