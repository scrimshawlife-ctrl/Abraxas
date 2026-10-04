"""Calibration Verifier for TRUTINA evidence."""

from __future__ import annotations

from typing import Dict, Any

from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType
from abraxas.evidence.verifiers.latent import compute_atomic_brier


class CalibrationVerifier:
    """Verifies calibration quality of Trutina Brier scoring evidence."""

    @property
    def evidence_type(self) -> str:
        return "CALIBRATION"

    @property
    def name(self) -> str:
        return "CalibrationVerifier"

    def __init__(
        self,
        max_brier_score: float = 0.25,
        max_reliability: float = 0.1,
        min_resolution: float = 0.1,
        max_uncertainty: float = 0.3,
    ):
        self.max_brier_score = max_brier_score
        self.max_reliability = max_reliability
        self.min_resolution = min_resolution
        self.max_uncertainty = max_uncertainty

    def verify(self, envelope: EvidenceEnvelope) -> Dict[str, Any]:
        """Verify calibration evidence quality."""
        if envelope.engine != "trutina":
            return {
                "passed": False,
                "escalate": True,
                "details": {"reason": "Engine is not trutina"}
            }

        brier_score = envelope.provenance.get("brier_score", 1.0)
        reliability = envelope.provenance.get("reliability", 1.0)
        resolution = envelope.provenance.get("resolution", 0.0)
        uncertainty = envelope.provenance.get("uncertainty", 1.0)
        calibration_method = envelope.provenance.get("calibration_method", "UNKNOWN")
        regimes_tested = envelope.provenance.get("regimes_tested", [])

        details = {
            "brier_score": brier_score,
            "reliability": reliability,
            "resolution": resolution,
            "uncertainty": uncertainty,
            "calibration_method": calibration_method,
            "regimes_tested": regimes_tested,
        }

        passed = (
            brier_score <= self.max_brier_score and
            reliability <= self.max_reliability and
            resolution >= self.min_resolution and
            uncertainty <= self.max_uncertainty
        )

        escalate = (
            brier_score > 0.35 or
            reliability > 0.25 or
            resolution < 0.05 or
            uncertainty > 0.5
        )

        return {
            "passed": passed,
            "escalate": escalate,
            "details": details
        }


# For backward compatibility with existing latent verifier
def compute_atomic_brier(expected_probability: float, observed_outcome: int | float) -> float:
    """Compute atomic Brier score."""
    o = int(observed_outcome)
    if o not in (0, 1):
        raise ValueError("observed_outcome must be 0 or 1")
    if not 0.0 <= expected_probability <= 1.0:
        raise ValueError("expected_probability out of [0,1]")
    return round((float(expected_probability) - o) ** 2, 6)


if __name__ == "__main__":
    print("CalibrationVerifier module loaded")