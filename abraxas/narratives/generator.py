"""Narrative Generator

Generates human-readable narratives from Oracle v2 and Phase Detection outputs.

Orchestrates:
- Template selection based on input type
- Data extraction from technical outputs
- Evidence aggregation and citation
- Narrative rendering with provenance
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from abraxas.core.provenance import Provenance
from abraxas.core.canonical import sha256_hex, canonical_json
from abraxas.narratives.templates import (
    PhaseTransitionTemplate,
    ResonanceSpikeTemplate,
    CascadeTrajectoryTemplate,
)


@dataclass(frozen=True)
class GeneratedNarrative:
    """Generated narrative with metadata."""

    narrative_id: str
    narrative_type: str  # "phase_transition", "resonance_spike", "cascade_trajectory"
    content: str  # The narrative text
    template_version: str
    generated_at_utc: str
    evidence_hashes: List[str]  # Referenced evidence bundles
    provenance: Optional[Provenance] = None

    def to_dict(self) -> Dict:
        return {
            "narrative_id": self.narrative_id,
            "narrative_type": self.narrative_type,
            "content": self.content,
            "template_version": self.template_version,
            "generated_at_utc": self.generated_at_utc,
            "evidence_hashes": self.evidence_hashes,
            "provenance": self.provenance.__dict__ if self.provenance else None,
        }


class NarrativeGenerator:
    """
    Narrative generator for Oracle v2 and Phase Detection outputs.

    Converts technical outputs into human-readable narratives using templates.
    """

    def __init__(self) -> None:
        """Initialize narrative generator with templates."""
        self._phase_template = PhaseTransitionTemplate()
        self._resonance_template = ResonanceSpikeTemplate()
        self._cascade_template = CascadeTrajectoryTemplate()

    def generate_phase_transition_narrative(
        self,
        warning: any,  # PhaseTransitionWarning from early_warning
        run_id: str = "NARRATIVE",
    ) -> GeneratedNarrative:
        """Generate narrative from phase transition warning.

        Args:
            warning: PhaseTransitionWarning object
            run_id: Run identifier for provenance

        Returns:
            GeneratedNarrative with human-readable content
        """
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Extract evidence hash
        evidence_hash = warning.provenance.inputs_hash if warning.provenance else "unknown"

        # Count tokens from evidence
        token_count = len(warning.evidence.get("observation_count", 0))

        # Render narrative
        content = self._phase_template.render(
            domain=warning.domain,
            current_phase=warning.current_phase,
            predicted_phase=warning.predicted_phase,
            estimated_hours=warning.estimated_hours,
            confidence=warning.confidence,
            token_count=token_count,
            evidence_hash=evidence_hash,
        )

        # Create provenance
        prov = Provenance(
            run_id=run_id,
            started_at_utc=timestamp,
            inputs_hash=sha256_hex(canonical_json({"warning_id": warning.warning_id})),
            config_hash=sha256_hex(canonical_json({"template": "phase_transition_v1"})),
        )

        narrative_id = f"NARR-PHASE-{warning.domain}-{timestamp[:10]}"

        return GeneratedNarrative(
            narrative_id=narrative_id,
            narrative_type="phase_transition",
            content=content,
            template_version=self._phase_template.template_version,
            generated_at_utc=timestamp,
            evidence_hashes=[evidence_hash],
            provenance=prov,
        )

    def generate_resonance_spike_narrative(
        self,
        alignment: any,  # PhaseAlignment from detector
        resonance_score: float,
        run_id: str = "NARRATIVE",
    ) -> GeneratedNarrative:
        """Generate narrative from phase alignment.

        Args:
            alignment: PhaseAlignment object
            resonance_score: Overall resonance score [0, 1]
            run_id: Run identifier for provenance

        Returns:
            GeneratedNarrative explaining resonance spike
        """
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Extract evidence hash
        evidence_hash = alignment.provenance.inputs_hash if alignment.provenance else "unknown"

        # Render narrative
        content = self._resonance_template.render(
            aligned_domains=list(alignment.domains),
            aligned_phase=alignment.aligned_phase,
            alignment_strength=alignment.alignment_strength,
            tokens_in_common=alignment.tokens_in_phase,
            resonance_score=resonance_score,
            evidence_hash=evidence_hash,
        )

        # Create provenance
        prov = Provenance(
            run_id=run_id,
            started_at_utc=timestamp,
            inputs_hash=sha256_hex(canonical_json({"alignment_id": alignment.alignment_id})),
            config_hash=sha256_hex(canonical_json({"template": "resonance_spike_v1"})),
        )

        narrative_id = f"NARR-RESONANCE-{'-'.join(sorted(alignment.domains))}-{timestamp[:10]}"

        return GeneratedNarrative(
            narrative_id=narrative_id,
            narrative_type="resonance_spike",
            content=content,
            template_version=self._resonance_template.template_version,
            generated_at_utc=timestamp,
            evidence_hashes=[evidence_hash],
            provenance=prov,
        )

    def generate_cascade_trajectory_narrative(
        self,
        coupling: any,  # DriftResonanceCoupling from coupling detector
        warnings: List[any],  # List of PhaseTransitionWarning objects
        run_id: str = "NARRATIVE",
    ) -> GeneratedNarrative:
        """Generate narrative from drift-resonance coupling.

        Args:
            coupling: DriftResonanceCoupling object
            warnings: List of active warnings
            run_id: Run identifier for provenance

        Returns:
            GeneratedNarrative with cascade trajectory summary
        """
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Extract evidence hash
        evidence_hash = coupling.provenance.inputs_hash if coupling.provenance else "unknown"

        # Convert warnings to simple dicts
        warning_dicts = [
            {
                "domain": w.domain,
                "predicted_phase": w.predicted_phase,
                "estimated_hours": w.estimated_hours,
                "confidence": w.confidence,
            }
            for w in warnings
        ]

        # Render narrative
        content = self._cascade_template.render(
            cascade_risk=coupling.cascade_risk,
            coupled_domains=list(coupling.domains),
            drift_strength=coupling.drift_strength,
            resonance_strength=coupling.resonance_strength,
            coupling_strength=coupling.coupling_strength,
            warnings=warning_dicts,
            evidence_hash=evidence_hash,
        )

        # Create provenance
        prov = Provenance(
            run_id=run_id,
            started_at_utc=timestamp,
            inputs_hash=sha256_hex(canonical_json({"coupling_id": coupling.coupling_id})),
            config_hash=sha256_hex(canonical_json({"template": "cascade_trajectory_v1"})),
        )

        narrative_id = f"NARR-CASCADE-{coupling.cascade_risk}-{timestamp[:10]}"

        # Collect all evidence hashes
        evidence_hashes = [evidence_hash]
        for w in warnings:
            if w.provenance:
                evidence_hashes.append(w.provenance.inputs_hash)

        return GeneratedNarrative(
            narrative_id=narrative_id,
            narrative_type="cascade_trajectory",
            content=content,
            template_version=self._cascade_template.template_version,
            generated_at_utc=timestamp,
            evidence_hashes=evidence_hashes,
            provenance=prov,
        )

    def generate_comprehensive_report(
        self,
        oracle_output: any,  # OracleV2Output
        alignments: List[any],  # PhaseAlignment objects
        warnings: List[any],  # PhaseTransitionWarning objects
        couplings: List[any],  # DriftResonanceCoupling objects
        run_id: str = "REPORT",
    ) -> str:
        """Generate comprehensive report from all inputs.

        Args:
            oracle_output: Oracle v2 output
            alignments: Phase alignments detected
            warnings: Active transition warnings
            couplings: Drift-resonance couplings
            run_id: Run identifier

        Returns:
            Comprehensive markdown report
        """
        lines = []
        lines.append("# Abraxas Intelligence Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
        lines.append(f"**Run ID:** {run_id}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Oracle Summary
        lines.append("## Oracle v2 Summary")
        lines.append("")
        lines.append(f"**Domain:** {oracle_output.compression.domain}")
        lines.append(f"**Tokens Analyzed:** {len(oracle_output.compression.compressed_tokens)}")
        lines.append(f"**Signals Detected:** {len(oracle_output.compression.domain_signals)}")
        lines.append(f"**Transparency (STI):** {oracle_output.compression.transparency_score:.2f}")
        lines.append(f"**Affect Direction:** {oracle_output.compression.affect_direction}")
        lines.append("")
        lines.append(f"**Forecast:** {len(oracle_output.forecast.phase_transitions)} phase transitions predicted")
        lines.append(f"**Weather:** {oracle_output.forecast.weather_trajectory}")
        lines.append(f"**Memetic Pressure:** {oracle_output.forecast.memetic_pressure:.2f}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Phase Alignments
        if alignments:
            lines.append(f"## Cross-Domain Alignments ({len(alignments)})")
            lines.append("")
            for alignment in alignments:
                narrative = self.generate_resonance_spike_narrative(
                    alignment,
                    resonance_score=oracle_output.forecast.resonance_score,
                    run_id=run_id
                )
                lines.append(narrative.content)
                lines.append("")

        # Warnings
        if warnings:
            lines.append(f"## Phase Transition Warnings ({len(warnings)})")
            lines.append("")
            for warning in warnings:
                narrative = self.generate_phase_transition_narrative(warning, run_id=run_id)
                lines.append(narrative.content)
                lines.append("")

        # Cascade Risk
        if couplings:
            lines.append(f"## Cascade Risk Assessment ({len(couplings)})")
            lines.append("")
            for coupling in couplings:
                narrative = self.generate_cascade_trajectory_narrative(
                    coupling, warnings, run_id=run_id
                )
                lines.append(narrative.content)
                lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("**Report Generated by Abraxas v1.5.0**")
        lines.append("*Deterministic symbolic intelligence with provenance-embedded forecasting*")
        lines.append("")

        return "\n".join(lines)


def create_narrative_generator() -> NarrativeGenerator:
    """Create narrative generator with default templates.

    Returns:
        Configured NarrativeGenerator
    """
    return NarrativeGenerator()
