"""Narrative Templates

Human-readable templates for converting technical outputs into narratives.

Design principles:
- Evidence-first: Every claim cites provenance
- No superlatives: "significant" not "massive", "detected" not "discovered"
- Deterministic: Same inputs → same narrative
- Professional tone: Technical clarity, no vibes
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class NarrativeTemplate:
    """Base narrative template."""

    template_id: str
    template_name: str
    template_version: str

    def render(self, **kwargs) -> str:
        """Render template with provided data."""
        raise NotImplementedError("Subclasses must implement render()")


@dataclass(frozen=True)
class PhaseTransitionTemplate(NarrativeTemplate):
    """Template for phase transition narratives.

    Converts lifecycle phase transitions into human-readable narratives.
    """

    template_id: str = "phase_transition_v1"
    template_name: str = "Phase Transition Narrative"
    template_version: str = "1.0.0"

    def render(
        self,
        domain: str,
        current_phase: str,
        predicted_phase: str,
        estimated_hours: float,
        confidence: float,
        token_count: int,
        evidence_hash: str,
    ) -> str:
        """Render phase transition narrative.

        Args:
            domain: Domain name (e.g., "politics")
            current_phase: Current lifecycle phase
            predicted_phase: Predicted next phase
            estimated_hours: Estimated hours to transition
            confidence: Confidence score [0, 1]
            token_count: Number of tokens in this phase
            evidence_hash: SHA-256 hash of evidence bundle

        Returns:
            Human-readable narrative with evidence citations
        """
        # Format confidence
        conf_pct = int(confidence * 100)
        conf_band = self._confidence_band(confidence)

        # Format timing
        time_str = self._format_hours(estimated_hours)

        # Build narrative
        lines = []
        lines.append(f"## Phase Transition Forecast: {domain.title()}")
        lines.append("")
        lines.append(f"**Current Phase:** {current_phase.title()}")
        lines.append(f"**Predicted Phase:** {predicted_phase.title()}")
        lines.append(f"**Estimated Time:** {time_str}")
        lines.append(f"**Confidence:** {conf_pct}% ({conf_band})")
        lines.append("")
        lines.append(f"### Analysis")
        lines.append("")
        lines.append(
            f"The {domain} domain is currently in the {current_phase} phase "
            f"with {token_count} tokens detected. Based on lifecycle dynamics, "
            f"a transition to {predicted_phase} phase is forecast within {time_str}."
        )
        lines.append("")
        lines.append(
            f"This forecast has {conf_band} confidence ({conf_pct}%) based on "
            f"tau velocity metrics and historical phase transition patterns."
        )
        lines.append("")
        lines.append(f"### Evidence")
        lines.append("")
        lines.append(f"**Provenance Hash:** `{evidence_hash[:16]}...`")
        lines.append(f"**Token Count:** {token_count}")
        lines.append(f"**Confidence Band:** {conf_band}")
        lines.append("")

        return "\n".join(lines)

    def _confidence_band(self, confidence: float) -> str:
        """Convert confidence to band label."""
        if confidence >= 0.8:
            return "HIGH"
        elif confidence >= 0.6:
            return "MEDIUM"
        elif confidence >= 0.4:
            return "LOW"
        else:
            return "VERY LOW"

    def _format_hours(self, hours: float) -> str:
        """Format hours as human-readable duration."""
        if hours < 24:
            return f"{int(hours)} hours"
        elif hours < 168:
            days = int(hours / 24)
            return f"{days} day{'s' if days > 1 else ''}"
        else:
            weeks = int(hours / 168)
            return f"{weeks} week{'s' if weeks > 1 else ''}"


@dataclass(frozen=True)
class ResonanceSpikeTemplate(NarrativeTemplate):
    """Template for resonance spike explanations.

    Explains why domains aligned and what it signals.
    """

    template_id: str = "resonance_spike_v1"
    template_name: str = "Resonance Spike Explanation"
    template_version: str = "1.0.0"

    def render(
        self,
        aligned_domains: List[str],
        aligned_phase: str,
        alignment_strength: float,
        tokens_in_common: Dict[str, List[str]],
        resonance_score: float,
        evidence_hash: str,
    ) -> str:
        """Render resonance spike narrative.

        Args:
            aligned_domains: List of aligned domains
            aligned_phase: The phase they're aligned in
            alignment_strength: Strength of alignment [0, 1]
            tokens_in_common: Domain → list of tokens in phase
            resonance_score: Overall resonance score [0, 1]
            evidence_hash: SHA-256 hash of evidence

        Returns:
            Human-readable explanation of alignment
        """
        domain_count = len(aligned_domains)
        strength_pct = int(alignment_strength * 100)
        resonance_pct = int(resonance_score * 100)

        # Build narrative
        lines = []
        lines.append(f"## Cross-Domain Resonance Spike")
        lines.append("")
        lines.append(f"**Aligned Domains:** {', '.join(d.title() for d in aligned_domains)}")
        lines.append(f"**Aligned Phase:** {aligned_phase.title()}")
        lines.append(f"**Alignment Strength:** {strength_pct}%")
        lines.append(f"**Resonance Score:** {resonance_pct}%")
        lines.append("")
        lines.append(f"### Why This Alignment Occurred")
        lines.append("")
        lines.append(
            f"{domain_count} domains have simultaneously entered the {aligned_phase} "
            f"phase, indicating cross-domain synchronization. This alignment suggests "
            f"shared lifecycle dynamics across symbolic domains."
        )
        lines.append("")

        # Common tokens section
        if tokens_in_common:
            lines.append(f"### Tokens in Phase")
            lines.append("")
            for domain in sorted(aligned_domains):
                tokens = tokens_in_common.get(domain, [])
                if tokens:
                    token_list = ", ".join(sorted(tokens)[:5])
                    if len(tokens) > 5:
                        token_list += f" (+{len(tokens) - 5} more)"
                    lines.append(f"- **{domain.title()}:** {token_list}")
            lines.append("")

        # Interpretation
        lines.append(f"### Signal Interpretation")
        lines.append("")
        if alignment_strength >= 0.7:
            lines.append(
                f"Strong alignment ({strength_pct}%) indicates significant cross-domain "
                f"synchronization. Monitor for potential cascade effects."
            )
        elif alignment_strength >= 0.5:
            lines.append(
                f"Moderate alignment ({strength_pct}%) suggests emerging cross-domain "
                f"patterns. Continue observation."
            )
        else:
            lines.append(
                f"Weak alignment ({strength_pct}%) may indicate coincidental timing "
                f"rather than structural coupling."
            )
        lines.append("")
        lines.append(f"### Evidence")
        lines.append("")
        lines.append(f"**Provenance Hash:** `{evidence_hash[:16]}...`")
        lines.append(f"**Domain Count:** {domain_count}")
        lines.append(f"**Total Tokens:** {sum(len(tokens_in_common.get(d, [])) for d in aligned_domains)}")
        lines.append("")

        return "\n".join(lines)


@dataclass(frozen=True)
class CascadeTrajectoryTemplate(NarrativeTemplate):
    """Template for cascade trajectory summaries.

    Summarizes predicted cascade paths and risk levels.
    """

    template_id: str = "cascade_trajectory_v1"
    template_name: str = "Cascade Trajectory Summary"
    template_version: str = "1.0.0"

    def render(
        self,
        cascade_risk: str,
        coupled_domains: List[str],
        drift_strength: float,
        resonance_strength: float,
        coupling_strength: float,
        warnings: List[Dict],
        evidence_hash: str,
    ) -> str:
        """Render cascade trajectory narrative.

        Args:
            cascade_risk: Risk level (LOW/MED/HIGH/CRITICAL)
            coupled_domains: Domains showing drift-resonance coupling
            drift_strength: Average drift strength [0, 1]
            resonance_strength: Average resonance strength [0, 1]
            coupling_strength: Coupling strength [0, 1]
            warnings: List of warning dicts
            evidence_hash: SHA-256 hash of evidence

        Returns:
            Human-readable cascade trajectory summary
        """
        drift_pct = int(drift_strength * 100)
        resonance_pct = int(resonance_strength * 100)
        coupling_pct = int(coupling_strength * 100)

        # Build narrative
        lines = []
        lines.append(f"## Cascade Risk Assessment")
        lines.append("")
        lines.append(f"**Risk Level:** {cascade_risk}")
        lines.append(f"**Coupled Domains:** {', '.join(d.title() for d in coupled_domains)}")
        lines.append(f"**Drift Strength:** {drift_pct}%")
        lines.append(f"**Resonance Strength:** {resonance_pct}%")
        lines.append(f"**Coupling Strength:** {coupling_pct}%")
        lines.append("")

        # Risk interpretation
        lines.append(f"### Risk Interpretation")
        lines.append("")
        if cascade_risk == "CRITICAL":
            lines.append(
                f"CRITICAL risk detected: Strong drift-resonance coupling ({coupling_pct}%) "
                f"across {len(coupled_domains)} domains indicates high cascade potential. "
                f"Immediate monitoring recommended."
            )
        elif cascade_risk == "HIGH":
            lines.append(
                f"HIGH risk detected: Drift-resonance coupling ({coupling_pct}%) suggests "
                f"elevated cascade potential. Enhanced monitoring advised."
            )
        elif cascade_risk == "MED":
            lines.append(
                f"MEDIUM risk detected: Moderate coupling ({coupling_pct}%) indicates "
                f"potential cascade formation. Continue standard monitoring."
            )
        else:
            lines.append(
                f"LOW risk: Coupling strength ({coupling_pct}%) below cascade threshold. "
                f"Standard observation protocols sufficient."
            )
        lines.append("")

        # Warnings section
        if warnings:
            lines.append(f"### Active Warnings ({len(warnings)})")
            lines.append("")
            for i, warning in enumerate(warnings[:5], 1):
                domain = warning.get("domain", "unknown")
                predicted = warning.get("predicted_phase", "unknown")
                hours = warning.get("estimated_hours", 0)
                conf = warning.get("confidence", 0)
                lines.append(
                    f"{i}. **{domain.title()}** → {predicted.title()} "
                    f"({self._format_hours(hours)}, {int(conf*100)}% confidence)"
                )
            if len(warnings) > 5:
                lines.append(f"... and {len(warnings) - 5} more warnings")
            lines.append("")

        # Evidence
        lines.append(f"### Evidence")
        lines.append("")
        lines.append(f"**Provenance Hash:** `{evidence_hash[:16]}...`")
        lines.append(f"**Domains Coupled:** {len(coupled_domains)}")
        lines.append(f"**Active Warnings:** {len(warnings)}")
        lines.append("")

        return "\n".join(lines)

    def _format_hours(self, hours: float) -> str:
        """Format hours as human-readable duration."""
        if hours < 24:
            return f"{int(hours)}h"
        elif hours < 168:
            return f"{int(hours/24)}d"
        else:
            return f"{int(hours/168)}w"


def create_phase_transition_template() -> PhaseTransitionTemplate:
    """Create phase transition template."""
    return PhaseTransitionTemplate()


def create_resonance_spike_template() -> ResonanceSpikeTemplate:
    """Create resonance spike template."""
    return ResonanceSpikeTemplate()


def create_cascade_trajectory_template() -> CascadeTrajectoryTemplate:
    """Create cascade trajectory template."""
    return CascadeTrajectoryTemplate()
