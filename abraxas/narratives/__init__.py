"""Resonance Narratives

Human-readable narrative generation from Oracle v2 and Phase Detection outputs.

This is an **output layer**, not core architecture:
- Consumes: Oracle v2 outputs, phase alignments, synchronicity patterns, warnings
- Produces: Human-readable narratives with evidence citations
- Purpose: External consumption, report generation, stakeholder communication

Templates:
- Phase transition narratives
- Resonance spike explanations
- Cascade trajectory summaries
- Evidence-grade artifact packaging
"""

from .templates import (
    NarrativeTemplate,
    PhaseTransitionTemplate,
    ResonanceSpikeTemplate,
    CascadeTrajectoryTemplate,
)
from .generator import (
    NarrativeGenerator,
    create_narrative_generator,
)
from .artifacts import (
    EvidenceArtifact,
    ArtifactPackager,
    create_artifact_packager,
)

__all__ = [
    # Templates
    "NarrativeTemplate",
    "PhaseTransitionTemplate",
    "ResonanceSpikeTemplate",
    "CascadeTrajectoryTemplate",
    # Generator
    "NarrativeGenerator",
    "create_narrative_generator",
    # Artifacts
    "EvidenceArtifact",
    "ArtifactPackager",
    "create_artifact_packager",
]
