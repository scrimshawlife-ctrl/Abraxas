"""Drift-Resonance Coupling Detector

Detects coupling between semantic drift and cross-domain resonance.

Key insight:
When drift (symbol meaning change) couples with resonance (cross-domain alignment),
cascade risk increases dramatically. This is a leading indicator of memetic storms.

Detection:
- Drift signals from semantic drift detection
- Resonance signals from Oracle v2 forecast phase
- Coupling = simultaneous high drift + high resonance
- Cascade risk = coupling strength × alignment breadth

Deterministic, evidence-based, no vibes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from abraxas.core.provenance import Provenance
from abraxas.core.canonical import sha256_hex, canonical_json


@dataclass(frozen=True)
class DriftResonanceCoupling:
    """Detected drift-resonance coupling event.

    When drift couples with resonance, cascade risk increases.
    """

    coupling_id: str
    timestamp_utc: str
    domains: tuple[str, ...]  # Domains in coupling
    drift_strength: float  # [0, 1]
    resonance_strength: float  # [0, 1]
    coupling_strength: float  # [0, 1] - product of drift × resonance
    cascade_risk: str  # LOW/MED/HIGH/CRITICAL
    tokens_drifting: Dict[str, List[str]]  # domain → drifting tokens
    evidence: Dict[str, any]
    provenance: Optional[Provenance] = None

    def to_dict(self) -> Dict:
        return {
            "coupling_id": self.coupling_id,
            "timestamp_utc": self.timestamp_utc,
            "domains": list(self.domains),
            "drift_strength": self.drift_strength,
            "resonance_strength": self.resonance_strength,
            "coupling_strength": self.coupling_strength,
            "cascade_risk": self.cascade_risk,
            "tokens_drifting": self.tokens_drifting,
            "evidence": self.evidence,
            "provenance": self.provenance.__dict__ if self.provenance else None,
        }


class CouplingDetector:
    """
    Detects drift-resonance coupling events.

    Coupling occurs when:
    1. Semantic drift is detected (symbol meaning changes)
    2. Cross-domain resonance is high (domains aligned)
    3. Both occur simultaneously

    When coupling occurs, cascade risk increases.
    """

    def __init__(
        self,
        drift_threshold: float = 0.6,
        resonance_threshold: float = 0.6,
        coupling_threshold: float = 0.5,
    ) -> None:
        """Initialize coupling detector.

        Args:
            drift_threshold: Minimum drift strength for coupling (default 0.6)
            resonance_threshold: Minimum resonance for coupling (default 0.6)
            coupling_threshold: Minimum coupling strength for detection (default 0.5)
        """
        self._drift_threshold = drift_threshold
        self._resonance_threshold = resonance_threshold
        self._coupling_threshold = coupling_threshold

    def detect_couplings(
        self,
        drift_signals: Dict[str, float],  # domain → drift_strength
        resonance_signals: Dict[str, float],  # domain → resonance_strength
        aligned_domains: Optional[List[str]] = None,  # Domains in current alignment
        drifting_tokens: Optional[Dict[str, List[str]]] = None,  # domain → tokens
        run_id: str = "COUPLING",
    ) -> List[DriftResonanceCoupling]:
        """Detect drift-resonance coupling events.

        Args:
            drift_signals: Drift strength per domain
            resonance_signals: Resonance strength per domain
            aligned_domains: Optional list of currently aligned domains
            drifting_tokens: Optional mapping of domain → drifting tokens
            run_id: Run identifier for provenance

        Returns:
            List of detected coupling events
        """
        couplings: List[DriftResonanceCoupling] = []
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Find domains with both high drift and high resonance
        coupled_domains = []

        for domain in drift_signals.keys():
            drift = drift_signals.get(domain, 0.0)
            resonance = resonance_signals.get(domain, 0.0)

            # Check if coupling occurs
            if drift >= self._drift_threshold and resonance >= self._resonance_threshold:
                coupling_strength = drift * resonance

                if coupling_strength >= self._coupling_threshold:
                    coupled_domains.append(domain)

        # If we have coupled domains, create coupling event
        if coupled_domains:
            # Aggregate strengths
            avg_drift = sum(drift_signals.get(d, 0.0) for d in coupled_domains) / len(
                coupled_domains
            )
            avg_resonance = sum(
                resonance_signals.get(d, 0.0) for d in coupled_domains
            ) / len(coupled_domains)
            coupling_strength = avg_drift * avg_resonance

            # Determine cascade risk
            cascade_risk = self._assess_cascade_risk(
                coupling_strength, len(coupled_domains), aligned_domains
            )

            # Build evidence
            evidence = {
                "drift_threshold": self._drift_threshold,
                "resonance_threshold": self._resonance_threshold,
                "coupled_domain_count": len(coupled_domains),
                "aligned_domain_count": len(aligned_domains) if aligned_domains else 0,
            }

            # Extract drifting tokens if provided
            tokens_dict = {}
            if drifting_tokens:
                tokens_dict = {
                    d: drifting_tokens.get(d, []) for d in coupled_domains
                }

            # Create provenance
            prov = Provenance(
                run_id=run_id,
                started_at_utc=timestamp,
                inputs_hash=sha256_hex(
                    canonical_json({
                        "drift_signals": drift_signals,
                        "resonance_signals": resonance_signals,
                    })
                ),
                config_hash=sha256_hex(
                    canonical_json({
                        "drift_threshold": self._drift_threshold,
                        "resonance_threshold": self._resonance_threshold,
                        "coupling_threshold": self._coupling_threshold,
                    })
                ),
            )

            coupling_id = f"COUPLING-{'-'.join(sorted(coupled_domains))}-{timestamp[:10]}"

            coupling = DriftResonanceCoupling(
                coupling_id=coupling_id,
                timestamp_utc=timestamp,
                domains=tuple(sorted(coupled_domains)),
                drift_strength=avg_drift,
                resonance_strength=avg_resonance,
                coupling_strength=coupling_strength,
                cascade_risk=cascade_risk,
                tokens_drifting=tokens_dict,
                evidence=evidence,
                provenance=prov,
            )

            couplings.append(coupling)

        return couplings

    def _assess_cascade_risk(
        self,
        coupling_strength: float,
        coupled_domain_count: int,
        aligned_domains: Optional[List[str]],
    ) -> str:
        """Assess cascade risk level based on coupling characteristics.

        Risk levels:
        - LOW: Weak coupling, few domains
        - MED: Moderate coupling or moderate breadth
        - HIGH: Strong coupling and/or high breadth
        - CRITICAL: Very strong coupling across many aligned domains
        """
        # Base risk on coupling strength
        if coupling_strength < 0.5:
            base_risk = "LOW"
        elif coupling_strength < 0.7:
            base_risk = "MED"
        elif coupling_strength < 0.85:
            base_risk = "HIGH"
        else:
            base_risk = "CRITICAL"

        # Amplify risk if many domains coupled
        if coupled_domain_count >= 4:
            if base_risk == "LOW":
                base_risk = "MED"
            elif base_risk == "MED":
                base_risk = "HIGH"
            elif base_risk == "HIGH":
                base_risk = "CRITICAL"

        # Amplify risk if aligned domains overlap with coupled domains
        if aligned_domains:
            overlap = len(set(aligned_domains))
            if overlap >= 3:
                if base_risk == "MED":
                    base_risk = "HIGH"
                elif base_risk == "HIGH":
                    base_risk = "CRITICAL"

        return base_risk


def create_coupling_detector(
    drift_threshold: float = 0.6,
    resonance_threshold: float = 0.6,
    coupling_threshold: float = 0.5,
) -> CouplingDetector:
    """Create coupling detector with default configuration.

    Args:
        drift_threshold: Minimum drift strength for coupling (default 0.6)
        resonance_threshold: Minimum resonance for coupling (default 0.6)
        coupling_threshold: Minimum coupling strength for detection (default 0.5)

    Returns:
        Configured CouplingDetector
    """
    return CouplingDetector(
        drift_threshold=drift_threshold,
        resonance_threshold=resonance_threshold,
        coupling_threshold=coupling_threshold,
    )
