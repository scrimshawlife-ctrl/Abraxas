"""Phase Alignment Detector

Detects when multiple domains enter the same lifecycle phase simultaneously.

Architecture:
- Tracks lifecycle states across domains
- Detects alignment events (2+ domains in same phase)
- Maps synchronicity patterns (domain X → domain Y coupling)
- Computes alignment strength and duration

Deterministic, provenance-tracked, no vibes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from abraxas.core.provenance import Provenance
from abraxas.core.canonical import sha256_hex, canonical_json


@dataclass(frozen=True)
class PhaseAlignment:
    """Cross-domain phase alignment event.

    Occurs when 2+ domains are in the same lifecycle phase.
    """

    alignment_id: str  # Unique identifier
    timestamp_utc: str
    aligned_phase: str  # The lifecycle phase (proto/front/saturated/dormant/archived)
    domains: Tuple[str, ...]  # Domains in alignment (sorted)
    alignment_strength: float  # [0, 1] - how strongly aligned
    duration_hours: Optional[float] = None  # Duration of alignment (if ended)
    tokens_in_phase: Dict[str, List[str]] = field(default_factory=dict)  # domain → tokens
    provenance: Optional[Provenance] = None

    def to_dict(self) -> Dict:
        return {
            "alignment_id": self.alignment_id,
            "timestamp_utc": self.timestamp_utc,
            "aligned_phase": self.aligned_phase,
            "domains": list(self.domains),
            "alignment_strength": self.alignment_strength,
            "duration_hours": self.duration_hours,
            "tokens_in_phase": self.tokens_in_phase,
            "provenance": self.provenance.__dict__ if self.provenance else None,
        }


@dataclass(frozen=True)
class SynchronicityPattern:
    """Synchronicity pattern between two domains.

    Tracks when domain X entering phase P predicts domain Y entering phase P.
    """

    source_domain: str  # Leading domain
    target_domain: str  # Following domain
    phase: str  # The phase being synchronized
    lag_hours: float  # Time lag (source → target)
    confidence: float  # [0, 1] - confidence in pattern
    observation_count: int  # Number of times observed
    last_observed_utc: str

    def to_dict(self) -> Dict:
        return {
            "source_domain": self.source_domain,
            "target_domain": self.target_domain,
            "phase": self.phase,
            "lag_hours": self.lag_hours,
            "confidence": self.confidence,
            "observation_count": self.observation_count,
            "last_observed_utc": self.last_observed_utc,
        }


@dataclass
class SynchronicityMap:
    """Map of all observed synchronicity patterns."""

    patterns: List[SynchronicityPattern]
    generated_utc: str
    provenance_hash: str

    def get_patterns_for_phase(self, phase: str) -> List[SynchronicityPattern]:
        """Get all patterns for a specific phase."""
        return [p for p in self.patterns if p.phase == phase]

    def get_leading_domain(self, phase: str) -> Optional[str]:
        """Get the domain that most often leads others into this phase."""
        patterns = self.get_patterns_for_phase(phase)
        if not patterns:
            return None

        # Count how often each domain appears as source
        source_counts: Dict[str, int] = {}
        for p in patterns:
            source_counts[p.source_domain] = source_counts.get(p.source_domain, 0) + 1

        # Return most frequent source
        return max(source_counts.items(), key=lambda x: x[1])[0]

    def predict_transition(
        self, domain: str, current_phase: str
    ) -> Optional[Tuple[str, float]]:
        """Predict next phase transition for domain based on synchronicity.

        Returns:
            (next_phase, hours) if prediction available, None otherwise
        """
        # Find patterns where this domain is the target
        candidate_patterns = [
            p for p in self.patterns
            if p.target_domain == domain and p.confidence > 0.5
        ]

        if not candidate_patterns:
            return None

        # Return highest confidence pattern
        best = max(candidate_patterns, key=lambda p: p.confidence)
        return (best.phase, best.lag_hours)

    def to_dict(self) -> Dict:
        return {
            "patterns": [p.to_dict() for p in self.patterns],
            "generated_utc": self.generated_utc,
            "provenance_hash": self.provenance_hash,
        }


class PhaseAlignmentDetector:
    """
    Detects cross-domain phase alignments and synchronicity patterns.

    Tracks:
    - When multiple domains are in the same lifecycle phase
    - Synchronicity patterns (domain X → domain Y lag)
    - Alignment strength and duration
    """

    def __init__(self, min_domains_for_alignment: int = 2) -> None:
        """Initialize phase alignment detector.

        Args:
            min_domains_for_alignment: Minimum domains required for alignment (default 2)
        """
        self._min_domains = min_domains_for_alignment
        self._alignment_history: List[PhaseAlignment] = []
        self._synchronicity_patterns: Dict[Tuple[str, str, str], SynchronicityPattern] = {}

    def detect_alignments(
        self,
        domain_states: Dict[str, Dict[str, str]],  # domain → {token → phase}
        timestamp_utc: Optional[str] = None,
        run_id: str = "DETECT",
    ) -> List[PhaseAlignment]:
        """Detect phase alignments across domains.

        Args:
            domain_states: Mapping of domain → {token → lifecycle_phase}
            timestamp_utc: Timestamp of detection (default: now)
            run_id: Run identifier for provenance

        Returns:
            List of detected phase alignments
        """
        if timestamp_utc is None:
            timestamp_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Group domains by phase
        phase_groups: Dict[str, List[str]] = {}  # phase → [domains]
        domain_tokens_by_phase: Dict[str, Dict[str, List[str]]] = {}  # phase → {domain → [tokens]}

        for domain, token_states in domain_states.items():
            # Count tokens in each phase for this domain
            phase_counts: Dict[str, int] = {}
            phase_tokens: Dict[str, List[str]] = {}

            for token, phase in token_states.items():
                phase_counts[phase] = phase_counts.get(phase, 0) + 1
                if phase not in phase_tokens:
                    phase_tokens[phase] = []
                phase_tokens[phase].append(token)

            # Assign domain to its dominant phase
            if phase_counts:
                dominant_phase = max(phase_counts.items(), key=lambda x: x[1])[0]

                if dominant_phase not in phase_groups:
                    phase_groups[dominant_phase] = []
                    domain_tokens_by_phase[dominant_phase] = {}

                phase_groups[dominant_phase].append(domain)
                domain_tokens_by_phase[dominant_phase][domain] = phase_tokens[dominant_phase]

        # Detect alignments (2+ domains in same phase)
        alignments: List[PhaseAlignment] = []

        for phase, domains in phase_groups.items():
            if len(domains) >= self._min_domains:
                # Compute alignment strength
                strength = self._compute_alignment_strength(
                    domains, domain_tokens_by_phase[phase]
                )

                # Create alignment
                alignment_id = f"ALIGN-{phase}-{'-'.join(sorted(domains))}-{timestamp_utc[:10]}"

                prov = Provenance(
                    run_id=run_id,
                    started_at_utc=timestamp_utc,
                    inputs_hash=sha256_hex(canonical_json(domain_states)),
                    config_hash=sha256_hex(canonical_json({"min_domains": self._min_domains})),
                )

                alignment = PhaseAlignment(
                    alignment_id=alignment_id,
                    timestamp_utc=timestamp_utc,
                    aligned_phase=phase,
                    domains=tuple(sorted(domains)),
                    alignment_strength=strength,
                    tokens_in_phase=domain_tokens_by_phase[phase],
                    provenance=prov,
                )

                alignments.append(alignment)
                self._alignment_history.append(alignment)

        return alignments

    def build_synchronicity_map(self, run_id: str = "SYNC") -> SynchronicityMap:
        """Build synchronicity map from alignment history.

        Analyzes historical alignments to detect patterns:
        - When domain X enters phase P, does domain Y follow?
        - What is the typical lag time?

        Returns:
            SynchronicityMap with all detected patterns
        """
        # Sort alignments by timestamp
        sorted_alignments = sorted(
            self._alignment_history,
            key=lambda a: a.timestamp_utc,
        )

        # Detect patterns by comparing consecutive alignments
        patterns: List[SynchronicityPattern] = []

        # Group alignments by phase
        by_phase: Dict[str, List[PhaseAlignment]] = {}
        for a in sorted_alignments:
            if a.aligned_phase not in by_phase:
                by_phase[a.aligned_phase] = []
            by_phase[a.aligned_phase].append(a)

        # For each phase, find domain ordering patterns
        for phase, alignments in by_phase.items():
            if len(alignments) < 2:
                continue

            # Compare consecutive alignments to find domain ordering
            for i in range(len(alignments) - 1):
                curr = alignments[i]
                next_align = alignments[i + 1]

                # Find domains that appear in next but not curr (following domains)
                curr_domains = set(curr.domains)
                next_domains = set(next_align.domains)

                leading_domains = curr_domains - next_domains
                following_domains = next_domains - curr_domains

                # Create patterns for each leading → following pair
                for source in leading_domains:
                    for target in following_domains:
                        # Compute lag (simplified - using string comparison)
                        lag_hours = self._compute_lag_hours(
                            curr.timestamp_utc, next_align.timestamp_utc
                        )

                        # Create or update pattern
                        pattern_key = (source, target, phase)

                        if pattern_key in self._synchronicity_patterns:
                            # Update existing pattern
                            existing = self._synchronicity_patterns[pattern_key]
                            # Average lag and increase confidence
                            new_lag = (
                                existing.lag_hours * existing.observation_count + lag_hours
                            ) / (existing.observation_count + 1)
                            new_confidence = min(
                                1.0, existing.confidence + 0.1
                            )  # Increase confidence

                            self._synchronicity_patterns[pattern_key] = SynchronicityPattern(
                                source_domain=source,
                                target_domain=target,
                                phase=phase,
                                lag_hours=new_lag,
                                confidence=new_confidence,
                                observation_count=existing.observation_count + 1,
                                last_observed_utc=next_align.timestamp_utc,
                            )
                        else:
                            # Create new pattern
                            self._synchronicity_patterns[pattern_key] = SynchronicityPattern(
                                source_domain=source,
                                target_domain=target,
                                phase=phase,
                                lag_hours=lag_hours,
                                confidence=0.5,  # Initial confidence
                                observation_count=1,
                                last_observed_utc=next_align.timestamp_utc,
                            )

        # Build map
        patterns_list = list(self._synchronicity_patterns.values())
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        prov_hash = sha256_hex(
            canonical_json({
                "patterns": [p.to_dict() for p in patterns_list],
                "timestamp": timestamp,
            })
        )

        return SynchronicityMap(
            patterns=patterns_list,
            generated_utc=timestamp,
            provenance_hash=prov_hash,
        )

    def _compute_alignment_strength(
        self, domains: List[str], domain_tokens: Dict[str, List[str]]
    ) -> float:
        """Compute alignment strength based on token overlap.

        Higher strength = more tokens in phase across domains.
        """
        if not domains:
            return 0.0

        # Compute average token count in phase
        token_counts = [len(domain_tokens.get(d, [])) for d in domains]
        avg_tokens = sum(token_counts) / len(token_counts)

        # Normalize to [0, 1] (assume max 20 tokens)
        return min(1.0, avg_tokens / 20.0)

    def _compute_lag_hours(self, timestamp1: str, timestamp2: str) -> float:
        """Compute lag in hours between two ISO timestamps."""
        try:
            t1 = datetime.fromisoformat(timestamp1.replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(timestamp2.replace("Z", "+00:00"))
            delta = abs((t2 - t1).total_seconds() / 3600.0)
            return delta
        except Exception:
            return 0.0


def create_phase_detector(min_domains_for_alignment: int = 2) -> PhaseAlignmentDetector:
    """Create phase alignment detector with default configuration.

    Args:
        min_domains_for_alignment: Minimum domains required for alignment (default 2)

    Returns:
        Configured PhaseAlignmentDetector
    """
    return PhaseAlignmentDetector(min_domains_for_alignment=min_domains_for_alignment)
