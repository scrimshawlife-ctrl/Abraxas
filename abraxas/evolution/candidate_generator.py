"""
Candidate Generator

Generates metric/operator/param_tweak candidates from domain deltas.

SOURCES:
- AALMANAC: Term velocity, frequency patterns
- MW: Semantic drift, cluster shifts
- INTEGRITY: SSI trends, trust surface changes
- BACKTEST: Failure analysis (from learning module)

CONSTRAINTS:
- Max 10 candidates per run
- Max 4 per source domain
- Must provide rationale and expected improvement
- Deterministic rules (no ML)
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from abraxas.evolution.schema import (
    MetricCandidate,
    CandidateKind,
    SourceDomain,
    generate_candidate_id,
    CandidateTarget
)


class CandidateGenerator:
    """Generate evolution candidates from domain deltas."""

    def __init__(
        self,
        max_candidates_per_run: int = 10,
        max_per_source: int = 4,
        min_priority: int = 5
    ):
        self.max_candidates_per_run = max_candidates_per_run
        self.max_per_source = max_per_source
        self.min_priority = min_priority

    def generate_candidates(
        self,
        aalmanac_deltas: Optional[Dict[str, Any]] = None,
        mw_deltas: Optional[Dict[str, Any]] = None,
        integrity_deltas: Optional[Dict[str, Any]] = None,
        backtest_failures: Optional[List[Dict[str, Any]]] = None,
        run_id: str = "manual"
    ) -> List[MetricCandidate]:
        """
        Generate candidates from all available deltas.

        Args:
            aalmanac_deltas: Term velocity and frequency data
            mw_deltas: Semantic drift and cluster data
            integrity_deltas: SSI and trust surface data
            backtest_failures: Failed backtest cases
            run_id: Identifier for this run

        Returns:
            List of MetricCandidate objects
        """
        all_candidates: List[MetricCandidate] = []

        # Generate from each source (max N per source)
        if aalmanac_deltas:
            candidates = self._generate_from_aalmanac(aalmanac_deltas)
            all_candidates.extend(candidates[:self.max_per_source])

        if mw_deltas:
            candidates = self._generate_from_mw(mw_deltas)
            all_candidates.extend(candidates[:self.max_per_source])

        if integrity_deltas:
            candidates = self._generate_from_integrity(integrity_deltas)
            all_candidates.extend(candidates[:self.max_per_source])

        if backtest_failures:
            candidates = self._generate_from_backtest(backtest_failures)
            all_candidates.extend(candidates[:self.max_per_source])

        # Sort by priority (highest first) and limit
        all_candidates.sort(key=lambda c: c.priority, reverse=True)
        all_candidates = all_candidates[:self.max_candidates_per_run]

        return all_candidates

    def _generate_from_aalmanac(self, deltas: Dict[str, Any]) -> List[MetricCandidate]:
        """
        Generate candidates from AALMANAC term velocity data.

        Rules:
        1. If term velocity exceeds threshold → propose term_coupling metric
        2. If frequency spike detected → propose frequency_damping param_tweak
        3. If rare term becoming common → propose vocabulary_expansion metric
        """
        candidates = []
        timestamp = datetime.now(timezone.utc).isoformat()
        target = CandidateTarget(
            portfolios=["slang_term_emergence", "short_term_core"],
            horizons=["H72H", "H30D"],
            score_metrics=["brier", "calibration_error"],
            improvement_thresholds={"brier": -0.003},
            no_regress_portfolios=["long_horizon_integrity"],
            mechanism=(
                "Improve short-term trigger recall/sharpness for emergent terms while "
                "not contaminating long-horizon regimes."
            ),
        )

        # Rule 1: Term velocity threshold
        term_velocities = deltas.get("term_velocities", {})
        for term, velocity_data in term_velocities.items():
            velocity = velocity_data.get("velocity", 0.0)
            if velocity > 0.8:  # High velocity threshold
                candidate_id = generate_candidate_id(
                    CandidateKind.METRIC,
                    SourceDomain.AALMANAC,
                    timestamp + term
                )

                candidates.append(MetricCandidate(
                    candidate_id=candidate_id,
                    kind=CandidateKind.METRIC,
                    source_domain=SourceDomain.AALMANAC,
                    proposed_at=timestamp,
                    proposed_by="aalmanac_term_velocity_analyzer",
                    name=f"term_coupling_{term}",
                    description=f"Track coupling between '{term}' and co-occurring terms",
                    rationale=f"Term '{term}' shows high velocity ({velocity:.2f}), "
                              f"suggesting it may be part of emerging narrative coupling",
                    implementation_spec={
                        "formula": "jaccard_similarity(term_context_A, term_context_B)",
                        "inputs": ["term_a", "term_b", "context_window"],
                        "output_range": [0.0, 1.0],
                        "computation": "local"
                    },
                    expected_improvement={
                        "brier_delta": -0.05,
                        "early_warning_improvement": 0.15
                    },
                    target_horizons=["H72H", "H30D"],
                    protected_horizons=["H90D", "H1Y"],
                    target=target,
                    priority=7
                ))

        # Rule 2: Frequency spike
        frequency_spikes = deltas.get("frequency_spikes", [])
        for spike in frequency_spikes:
            term = spike.get("term")
            spike_ratio = spike.get("spike_ratio", 1.0)

            if spike_ratio > 3.0:  # 3x normal frequency
                candidate_id = generate_candidate_id(
                    CandidateKind.PARAM_TWEAK,
                    SourceDomain.AALMANAC,
                    timestamp + term
                )

                candidates.append(MetricCandidate(
                    candidate_id=candidate_id,
                    kind=CandidateKind.PARAM_TWEAK,
                    source_domain=SourceDomain.AALMANAC,
                    proposed_at=timestamp,
                    proposed_by="aalmanac_frequency_spike_detector",
                    name=f"frequency_damping_{term}",
                    description=f"Dampen influence of high-frequency term '{term}'",
                    rationale=f"Term '{term}' shows {spike_ratio:.1f}x spike, "
                              f"may indicate manipulation or spam amplification",
                    param_path=f"aalmanac.frequency_damping.{term}",
                    current_value=1.0,
                    proposed_value=0.5,  # Reduce influence by 50%
                    expected_improvement={
                        "false_positive_reduction": 0.20,
                        "SSI_correlation": 0.15
                    },
                    target_horizons=["H72H"],
                    protected_horizons=["H30D", "H90D"],
                    target=target,
                    priority=6
                ))

        return candidates

    def _generate_from_mw(self, deltas: Dict[str, Any]) -> List[MetricCandidate]:
        """
        Generate candidates from Meaning Weave semantic drift.

        Rules:
        1. If synthetic_saturation rising → propose SSI dampening param_tweak
        2. If cluster split detected → propose cluster_stability metric
        3. If semantic drift accelerating → propose drift_velocity metric
        """
        candidates = []
        timestamp = datetime.now(timezone.utc).isoformat()
        integrity_target = CandidateTarget(
            portfolios=["long_horizon_integrity"],
            horizons=["H1Y", "H5Y"],
            score_metrics=["coverage_rate", "crps_avg", "trend_acc"],
            improvement_thresholds={"coverage_rate": 0.02},
            no_regress_portfolios=["short_term_core"],
            mechanism=(
                "Reduce SSI poisoning of long-horizon regime updates; widen uncertainty "
                "during drift."
            ),
        )
        ssi_dampening_target = CandidateTarget(
            portfolios=["long_horizon_integrity"],
            horizons=["H1Y", "H5Y"],
            score_metrics=["coverage_rate"],
            improvement_thresholds={"coverage_rate": 0.03},
            no_regress_portfolios=["short_term_core"],
            mechanism=(
                "Reduce SSI poisoning of long-horizon regime updates; widen uncertainty "
                "during drift."
            ),
        )

        # Rule 1: Synthetic saturation rising
        synthetic_saturation = deltas.get("synthetic_saturation", {})
        ssi_delta = synthetic_saturation.get("delta", 0.0)
        current_ssi = synthetic_saturation.get("current", 0.5)

        if ssi_delta > 0.15:  # 15% increase in SSI
            candidate_id = generate_candidate_id(
                CandidateKind.PARAM_TWEAK,
                SourceDomain.MW,
                timestamp
            )

            candidates.append(MetricCandidate(
                candidate_id=candidate_id,
                kind=CandidateKind.PARAM_TWEAK,
                source_domain=SourceDomain.MW,
                proposed_at=timestamp,
                proposed_by="mw_synthetic_saturation_monitor",
                name="ssi_dampening_multiplier",
                description="Increase SSI dampening for forecast probability updates",
                rationale=f"SSI increased by {ssi_delta:.2f} (now {current_ssi:.2f}), "
                          f"suggesting higher synthetic content ratio",
                param_path="forecast.ssi_dampening_multiplier",
                current_value=1.0,
                proposed_value=1.3,  # Increase dampening by 30%
                expected_improvement={
                    "brier_delta": -0.03,
                    "manipulation_resistance": 0.25
                },
                target_horizons=["H72H", "H30D"],
                protected_horizons=["H90D"],
                target=ssi_dampening_target,
                priority=8
            ))

        # Rule 2: Cluster split
        cluster_splits = deltas.get("cluster_splits", [])
        for split in cluster_splits:
            cluster_id = split.get("cluster_id")
            split_confidence = split.get("confidence", 0.0)

            if split_confidence > 0.7:
                candidate_id = generate_candidate_id(
                    CandidateKind.METRIC,
                    SourceDomain.MW,
                    timestamp + cluster_id
                )

                candidates.append(MetricCandidate(
                    candidate_id=candidate_id,
                    kind=CandidateKind.METRIC,
                    source_domain=SourceDomain.MW,
                    proposed_at=timestamp,
                    proposed_by="mw_cluster_split_detector",
                    name=f"cluster_stability_{cluster_id}",
                    description=f"Track stability of cluster '{cluster_id}'",
                    rationale=f"Cluster '{cluster_id}' split with {split_confidence:.2f} confidence, "
                              f"may indicate narrative bifurcation",
                    implementation_spec={
                        "formula": "1 - avg_distance_to_centroid",
                        "inputs": ["cluster_members", "centroid"],
                        "output_range": [0.0, 1.0],
                        "computation": "local"
                    },
                    expected_improvement={
                        "narrative_detection_delta": 0.18,
                        "false_alarm_reduction": 0.10
                    },
                    target_horizons=["H30D", "H90D"],
                    protected_horizons=["H1Y"],
                    target=integrity_target,
                    priority=6
                ))

        return candidates

    def _generate_from_integrity(self, deltas: Dict[str, Any]) -> List[MetricCandidate]:
        """
        Generate candidates from Integrity system deltas.

        Rules:
        1. If SSI rising rapidly → propose confidence threshold param_tweak
        2. If trust surface declining → propose trust_floor metric
        3. If IRI volatility high → propose stability_window param_tweak
        """
        candidates = []
        timestamp = datetime.now(timezone.utc).isoformat()
        integrity_target = CandidateTarget(
            portfolios=["long_horizon_integrity"],
            horizons=["H1Y", "H5Y"],
            score_metrics=["coverage_rate", "crps_avg", "trend_acc"],
            improvement_thresholds={"coverage_rate": 0.02},
            no_regress_portfolios=["short_term_core"],
            mechanism=(
                "Reduce SSI poisoning of long-horizon regime updates; widen uncertainty "
                "during drift."
            ),
        )

        # Rule 1: SSI rising rapidly
        ssi_trend = deltas.get("ssi_trend", {})
        ssi_velocity = ssi_trend.get("velocity", 0.0)
        current_ssi = ssi_trend.get("current", 0.5)

        if ssi_velocity > 0.10:  # 10% per period
            candidate_id = generate_candidate_id(
                CandidateKind.PARAM_TWEAK,
                SourceDomain.INTEGRITY,
                timestamp
            )

            candidates.append(MetricCandidate(
                candidate_id=candidate_id,
                kind=CandidateKind.PARAM_TWEAK,
                source_domain=SourceDomain.INTEGRITY,
                proposed_at=timestamp,
                proposed_by="integrity_ssi_velocity_monitor",
                name="confidence_threshold_H72H",
                description="Raise confidence threshold for H72H forecasts",
                rationale=f"SSI rising at {ssi_velocity:.2f}/period (now {current_ssi:.2f}), "
                          f"requires higher confidence threshold to maintain accuracy",
                param_path="forecast.confidence_threshold.H72H",
                current_value=0.65,
                proposed_value=0.75,  # Increase threshold by 0.10
                expected_improvement={
                    "false_positive_reduction": 0.15,
                    "precision_delta": 0.08
                },
                target_horizons=["H72H"],
                protected_horizons=["H30D", "H90D"],
                target=integrity_target,
                priority=7
            ))

        # Rule 2: Trust surface declining
        trust_surface = deltas.get("trust_surface", {})
        trust_delta = trust_surface.get("delta", 0.0)
        current_trust = trust_surface.get("current", 0.8)

        if trust_delta < -0.20:  # 20% decline
            candidate_id = generate_candidate_id(
                CandidateKind.METRIC,
                SourceDomain.INTEGRITY,
                timestamp
            )

            candidates.append(MetricCandidate(
                candidate_id=candidate_id,
                kind=CandidateKind.METRIC,
                source_domain=SourceDomain.INTEGRITY,
                proposed_at=timestamp,
                proposed_by="integrity_trust_surface_monitor",
                name="trust_floor_metric",
                description="Track minimum trust level across signal sources",
                rationale=f"Trust surface declined by {abs(trust_delta):.2f} (now {current_trust:.2f}), "
                          f"need metric to track floor and prevent cascade",
                implementation_spec={
                    "formula": "min(source_trust_scores) over tau_window",
                    "inputs": ["source_trust_scores", "tau_window"],
                    "output_range": [0.0, 1.0],
                    "computation": "local"
                },
                expected_improvement={
                    "early_warning_delta": 0.20,
                    "cascade_prevention": 0.30
                },
                target_horizons=["H72H", "H30D", "H90D"],
                protected_horizons=[],
                target=integrity_target,
                priority=9  # High priority for trust issues
            ))

        return candidates

    def _generate_from_backtest(self, failures: List[Dict[str, Any]]) -> List[MetricCandidate]:
        """
        Generate candidates from backtest failures.

        Rules:
        1. If repeated MISS on same trigger type → propose threshold adjustment
        2. If ABSTAIN rate high → propose new operator for missing signal
        3. If temporal gap detected → propose tau adjustment
        """
        candidates = []
        timestamp = datetime.now(timezone.utc).isoformat()

        # Rule 1: Repeated MISS on trigger type
        trigger_failure_counts = {}
        for failure in failures:
            trigger_kind = failure.get("trigger_kind")
            if trigger_kind:
                trigger_failure_counts[trigger_kind] = trigger_failure_counts.get(trigger_kind, 0) + 1

        for trigger_kind, count in trigger_failure_counts.items():
            if count >= 3:  # 3+ failures on same trigger type
                candidate_id = generate_candidate_id(
                    CandidateKind.PARAM_TWEAK,
                    SourceDomain.BACKTEST,
                    timestamp + trigger_kind
                )

                candidates.append(MetricCandidate(
                    candidate_id=candidate_id,
                    kind=CandidateKind.PARAM_TWEAK,
                    source_domain=SourceDomain.BACKTEST,
                    proposed_at=timestamp,
                    proposed_by="backtest_failure_analyzer",
                    name=f"threshold_relax_{trigger_kind}",
                    description=f"Relax threshold for '{trigger_kind}' triggers",
                    rationale=f"Detected {count} MISS failures on '{trigger_kind}' triggers, "
                              f"threshold may be too aggressive",
                    param_path=f"backtest.triggers.{trigger_kind}.threshold_multiplier",
                    current_value=1.0,
                    proposed_value=0.8,  # Relax by 20%
                    expected_improvement={
                        "hit_rate_delta": 0.15,
                        "miss_rate_reduction": 0.10
                    },
                    target_horizons=["H72H", "H30D"],
                    protected_horizons=["H90D"],
                    priority=6
                ))

        return candidates


# Helper functions for external use

def generate_candidates_from_deltas(
    aalmanac_deltas: Optional[Dict[str, Any]] = None,
    mw_deltas: Optional[Dict[str, Any]] = None,
    integrity_deltas: Optional[Dict[str, Any]] = None,
    backtest_failures: Optional[List[Dict[str, Any]]] = None,
    run_id: str = "manual",
    max_candidates: int = 10
) -> List[MetricCandidate]:
    """
    Convenience function to generate candidates from all available deltas.

    Args:
        aalmanac_deltas: Term velocity and frequency data
        mw_deltas: Semantic drift and cluster data
        integrity_deltas: SSI and trust surface data
        backtest_failures: Failed backtest cases
        run_id: Identifier for this run
        max_candidates: Maximum candidates to return

    Returns:
        List of MetricCandidate objects
    """
    generator = CandidateGenerator(max_candidates_per_run=max_candidates)
    return generator.generate_candidates(
        aalmanac_deltas=aalmanac_deltas,
        mw_deltas=mw_deltas,
        integrity_deltas=integrity_deltas,
        backtest_failures=backtest_failures,
        run_id=run_id
    )


# Example usage
if __name__ == "__main__":
    # Example: Generate candidates from synthetic deltas
    aalmanac_deltas = {
        "term_velocities": {
            "deepfake": {"velocity": 0.85, "frequency": 120},
            "propaganda": {"velocity": 0.65, "frequency": 80}
        },
        "frequency_spikes": [
            {"term": "misinformation", "spike_ratio": 4.5}
        ]
    }

    mw_deltas = {
        "synthetic_saturation": {"delta": 0.18, "current": 0.62},
        "cluster_splits": [
            {"cluster_id": "cluster_integrity_001", "confidence": 0.75}
        ]
    }

    integrity_deltas = {
        "ssi_trend": {"velocity": 0.12, "current": 0.58},
        "trust_surface": {"delta": -0.25, "current": 0.72}
    }

    candidates = generate_candidates_from_deltas(
        aalmanac_deltas=aalmanac_deltas,
        mw_deltas=mw_deltas,
        integrity_deltas=integrity_deltas,
        run_id="test_run_001"
    )

    print(f"Generated {len(candidates)} candidates:")
    for i, cand in enumerate(candidates, 1):
        print(f"\n{i}. {cand.name}")
        print(f"   Kind: {cand.kind.value}")
        print(f"   Source: {cand.source_domain.value}")
        print(f"   Priority: {cand.priority}")
        print(f"   Rationale: {cand.rationale[:80]}...")
