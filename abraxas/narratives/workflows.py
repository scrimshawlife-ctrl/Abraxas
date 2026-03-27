"""Narrative Workflows

High-level orchestration for resonance narrative generation and evidence-grade packaging.

Purpose:
- Generate narrative sets in one deterministic pass
- Package narrative outputs with provenance chains
- Optionally export JSON/Markdown artifacts
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from abraxas.narratives.artifacts import ArtifactPackager, EvidenceArtifact
from abraxas.narratives.generator import GeneratedNarrative, NarrativeGenerator
from abraxas.phase.coupling import DriftResonanceCoupling
from abraxas.phase.detector import PhaseAlignment
from abraxas.phase.early_warning import PhaseTransitionWarning

if TYPE_CHECKING:
    from abraxas.oracle.v2.pipeline import OracleV2Output


@dataclass(frozen=True)
class WorkflowResult:
    """Result bundle returned by narrative workflow."""

    narratives: List[GeneratedNarrative]
    report: str
    artifacts: List[EvidenceArtifact]
    exported_paths: Dict[str, Dict[str, Path]]


def build_resonance_narrative_artifacts(
    *,
    oracle_output: "OracleV2Output",
    alignments: List[PhaseAlignment],
    warnings: List[PhaseTransitionWarning],
    couplings: List[DriftResonanceCoupling],
    run_id: str,
    output_dir: Optional[Path] = None,
    export_formats: Optional[List[str]] = None,
    generator: Optional[NarrativeGenerator] = None,
    packager: Optional[ArtifactPackager] = None,
) -> WorkflowResult:
    """Generate and package resonance narratives in one pass.

    This workflow advances roadmap output-layer tasks by producing:
    - Resonance spike explanations
    - Phase transition narratives
    - Cascade trajectory summaries
    - Evidence-grade packaged artifacts
    """
    generator = generator or NarrativeGenerator()
    packager = packager or ArtifactPackager()

    narrative_items: List[GeneratedNarrative] = []

    for alignment in alignments:
        narrative_items.append(
            generator.generate_resonance_spike_narrative(
                alignment,
                resonance_score=oracle_output.forecast.resonance_score,
                run_id=run_id,
            )
        )

    for warning in warnings:
        narrative_items.append(generator.generate_phase_transition_narrative(warning, run_id=run_id))

    for coupling in couplings:
        narrative_items.append(
            generator.generate_cascade_trajectory_narrative(coupling, warnings, run_id=run_id)
        )

    report = generator.generate_comprehensive_report(
        oracle_output=oracle_output,
        alignments=alignments,
        warnings=warnings,
        couplings=couplings,
        run_id=run_id,
    )

    artifacts: List[EvidenceArtifact] = [packager.package_narrative(n) for n in narrative_items]
    artifacts.append(packager.package_comprehensive_report(report, narrative_items, run_id=run_id))

    exported_paths: Dict[str, Dict[str, Path]] = {}
    if output_dir is not None:
        formats = export_formats or ["json", "md"]
        key_counts: Dict[str, int] = {}
        for artifact in artifacts:
            key = _build_export_key(artifact.artifact_id, key_counts)
            exported_paths[key] = packager.export_artifact(
                artifact=artifact,
                output_dir=output_dir,
                formats=formats,
            )

    return WorkflowResult(
        narratives=narrative_items,
        report=report,
        artifacts=artifacts,
        exported_paths=exported_paths,
    )


def _build_export_key(artifact_id: str, key_counts: Dict[str, int]) -> str:
    """Return deterministic, collision-free key for exported artifact map."""
    current_count = key_counts.get(artifact_id, 0) + 1
    key_counts[artifact_id] = current_count
    if current_count == 1:
        return artifact_id
    return f"{artifact_id}__{current_count}"
