"""NCP (Narrative Cascade Predictor): Predicts cascade scenarios from τ + D/M inputs.

Input: τ snapshots + AAlmanac + Weather + D/M metrics
Output: Scenario envelopes (top-N cascade paths)

Each path includes:
- Trigger (initiating event)
- Probability [0,1] (deterministic heuristic score, normalized)
- Duration estimate
- Intermediate states
- Terminus (final state)

Probabilities are deterministic heuristic scores, not stochastic simulations.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import uuid4

from abraxas.core.provenance import Provenance
from abraxas.sod.models import SODInput, ScenarioEnvelope, ScenarioPath


class NarrativeCascadePredictor:
    """
    Narrative Cascade Predictor (NCP).

    Generates deterministic scenario envelopes from SOD inputs.
    v1.4: Scaffold only, no simulation engine.
    """

    def __init__(
        self,
        *,
        top_k: int = 5,
        min_probability: float = 0.1,
        git_sha: Optional[str] = None,
        host: Optional[str] = None,
    ):
        """
        Initialize NCP.

        Args:
            top_k: Number of top paths to return
            min_probability: Minimum probability threshold for path inclusion
            git_sha: Git SHA for provenance
            host: Host identifier for provenance
        """
        self.top_k = top_k
        self.min_probability = min_probability
        self._git_sha = git_sha
        self._host = host

    def predict(
        self,
        sod_input: SODInput,
        *,
        run_id: Optional[str] = None,
    ) -> ScenarioEnvelope:
        """
        Predict cascade scenarios from SOD input.

        Args:
            sod_input: SOD input bundle
            run_id: Optional run identifier

        Returns:
            ScenarioEnvelope with top-K paths and falsifiers
        """
        tau = sod_input.tau_snapshot
        risk = sod_input.risk_indices
        affinity = sod_input.affinity_score

        # Generate candidate paths (deterministic heuristics)
        candidate_paths = self._generate_candidate_paths(tau, risk, affinity)

        # Sort by probability and take top-K
        sorted_paths = sorted(
            candidate_paths, key=lambda p: p.probability, reverse=True
        )
        top_paths = [p for p in sorted_paths[: self.top_k] if p.probability >= self.min_probability]

        # Generate falsifiers
        falsifiers = self._generate_falsifiers(tau, risk)

        # Compute confidence
        confidence = self._compute_confidence(tau, risk)

        # Build provenance
        prov = self._build_provenance(run_id, sod_input)

        scenario_id = str(uuid4())
        return ScenarioEnvelope(
            scenario_id=scenario_id,
            paths=top_paths,
            falsifiers=falsifiers,
            confidence=confidence,
            provenance=prov,
        )

    def _generate_candidate_paths(
        self, tau, risk, affinity
    ) -> List[ScenarioPath]:
        """Generate candidate cascade paths (deterministic heuristics)."""
        paths = []

        # Path 1: Viral spread (high τᵥ, low IRI)
        if tau.tau_velocity > 0.5:
            prob = min(tau.tau_velocity / 2.0, 1.0)
            if risk:
                prob *= 1.0 - (risk.iri / 200.0)  # Reduce if high IRI
            paths.append(
                ScenarioPath(
                    path_id=f"viral-{uuid4().hex[:8]}",
                    trigger="High emergence velocity detected",
                    probability=prob,
                    duration_hours=48,
                    intermediates=["Proto", "Front", "Early Saturation"],
                    terminus="Saturated",
                )
            )

        # Path 2: Coordinated amplification (high MRI, high CUS)
        if risk and risk.mri > 60 and risk.network_campaign.cus > 0.7:
            prob = (risk.mri / 100.0) * risk.network_campaign.cus
            paths.append(
                ScenarioPath(
                    path_id=f"coord-{uuid4().hex[:8]}",
                    trigger="Coordinated amplification campaign detected",
                    probability=prob,
                    duration_hours=72,
                    intermediates=["Coordinated Injection", "Multi-Platform Spread", "Peak Saturation"],
                    terminus="Saturated (Artificial)",
                )
            )

        # Path 3: Slow decay (low τᵥ, high τₕ)
        if tau.tau_velocity < 0.1 and tau.tau_half_life > 168:
            prob = min(tau.tau_half_life / 500.0, 1.0)
            paths.append(
                ScenarioPath(
                    path_id=f"decay-{uuid4().hex[:8]}",
                    trigger="Stable but stagnant symbol",
                    probability=prob,
                    duration_hours=336,  # 2 weeks
                    intermediates=["Saturated", "Early Dormant", "Late Dormant"],
                    terminus="Archived",
                )
            )

        # Path 4: Rapid collapse (high IRI, declining engagement)
        if risk and risk.iri > 70:
            prob = risk.iri / 100.0
            paths.append(
                ScenarioPath(
                    path_id=f"collapse-{uuid4().hex[:8]}",
                    trigger="Integrity failure detected",
                    probability=prob,
                    duration_hours=24,
                    intermediates=["Front", "Credibility Loss", "Rapid Dormant"],
                    terminus="Archived",
                )
            )

        # Path 5: Revival wave (mutation evidence + positive velocity)
        if tau.tau_velocity > 0.3 and tau.tau_half_life < 48:
            prob = tau.tau_velocity / 5.0
            paths.append(
                ScenarioPath(
                    path_id=f"revival-{uuid4().hex[:8]}",
                    trigger="Revival wave (mutation-driven)",
                    probability=prob,
                    duration_hours=120,
                    intermediates=["Dormant", "Proto (Revival)", "Front"],
                    terminus="Saturated",
                )
            )

        return paths

    def _generate_falsifiers(self, tau, risk) -> List[str]:
        """Generate counterfactual falsifiers."""
        falsifiers = []

        # Falsifier 1: Velocity reversal
        if tau.tau_velocity > 0:
            falsifiers.append(
                f"Velocity reversal: τᵥ becomes negative (currently {tau.tau_velocity:.2f})"
            )

        # Falsifier 2: Integrity restoration
        if risk and risk.iri > 50:
            falsifiers.append(
                f"Integrity restoration: IRI drops below 30 (currently {risk.iri:.1f})"
            )

        # Falsifier 3: Platform intervention
        falsifiers.append("Platform intervention: Content removal or throttling")

        return falsifiers

    def _compute_confidence(self, tau, risk) -> str:
        """Compute confidence level."""
        # Confidence based on tau confidence and risk confidence
        if tau.confidence.value == "LOW":
            return "LOW"
        if risk and risk.confidence.value == "LOW":
            return "LOW"
        if tau.confidence.value == "HIGH" and (not risk or risk.confidence.value == "HIGH"):
            return "HIGH"
        return "MED"

    def _build_provenance(self, run_id, sod_input) -> Provenance:
        """Build provenance record."""
        from abraxas.core.canonical import canonical_json, sha256_hex

        inputs_obj = {
            "tau_snapshot": {
                "tau_half_life": sod_input.tau_snapshot.tau_half_life,
                "tau_velocity": sod_input.tau_snapshot.tau_velocity,
                "tau_phase_proximity": sod_input.tau_snapshot.tau_phase_proximity,
            },
            "risk_indices": {
                "iri": sod_input.risk_indices.iri if sod_input.risk_indices else None,
                "mri": sod_input.risk_indices.mri if sod_input.risk_indices else None,
            } if sod_input.risk_indices else None,
        }

        inputs_hash = sha256_hex(canonical_json(inputs_obj))
        config_hash = sha256_hex(
            canonical_json({
                "module": "NCP.v1",
                "top_k": self.top_k,
                "min_probability": self.min_probability,
            })
        )

        return Provenance(
            run_id=run_id or "ncp-run",
            started_at_utc=Provenance.now_iso_z(),
            inputs_hash=inputs_hash,
            config_hash=config_hash,
            git_sha=self._git_sha,
            host=self._host,
        )
