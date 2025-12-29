"""Metric Evaluation Harness

Deterministic evaluation of candidate metrics through promotion gates:
1. Provenance Gate
2. Falsifiability Gate
3. Non-Redundancy Gate
4. Rent-Payment Gate
5. Ablation Gate
6. Stabilization Gate
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Optional, Tuple

from abraxas.metrics.governance import (
    CandidateMetric,
    EvidenceBundle,
    LiftMetrics,
    RedundancyScores,
    StabilizationScores,
    TestResults,
)


class MetricEvaluator:
    """Deterministic evaluation harness for candidate metrics."""

    def __init__(self, sim_version: str = "1.0.0"):
        self.sim_version = sim_version

    def evaluate_provenance_gate(self, candidate: CandidateMetric) -> bool:
        """Gate 1: Provenance - all required fields present and valid.

        Checks:
        - metric_id, description, units, valid_range present
        - compute_fn reference exists
        - input_sources declared with hashes
        - All fields non-empty

        Args:
            candidate: Candidate metric

        Returns:
            True if passed, False otherwise
        """
        prov = candidate.provenance

        # Check required fields
        if not prov.metric_id or not prov.description or not prov.units:
            return False

        if not prov.compute_fn:
            return False

        if "min" not in prov.valid_range or "max" not in prov.valid_range:
            return False

        if prov.valid_range["min"] >= prov.valid_range["max"]:
            return False

        # Check input sources declared
        if not prov.input_sources:
            return False

        # Each input source must have 'source' and 'hash' keys
        for src in prov.input_sources:
            if "source" not in src or "hash" not in src:
                return False

        return True

    def evaluate_falsifiability_gate(self, candidate: CandidateMetric) -> bool:
        """Gate 2: Falsifiability - metric can be proven wrong.

        Checks:
        - predictions_influenced declared (non-empty)
        - disconfirmation_criteria declared
        - evaluation_window specified

        Args:
            candidate: Candidate metric

        Returns:
            True if passed, False otherwise
        """
        fals = candidate.falsifiability

        # Must influence at least one prediction
        if not fals.predictions_influenced:
            return False

        # Must have disconfirmation criteria
        if not fals.disconfirmation_criteria:
            return False

        # Evaluation window must be positive
        if fals.evaluation_window <= 0:
            return False

        return True

    def evaluate_redundancy_gate(
        self,
        candidate: CandidateMetric,
        candidate_values: np.ndarray,
        canonical_metrics: Dict[str, np.ndarray],
        max_corr_threshold: float = 0.85,
    ) -> Tuple[bool, RedundancyScores]:
        """Gate 3: Non-Redundancy - not highly correlated with canonical metrics.

        Checks:
        - Pearson correlation with all canonical metrics
        - Mutual information (approximated via binning)
        - Identifies nearest metrics

        Args:
            candidate: Candidate metric
            candidate_values: Time series of candidate metric values
            canonical_metrics: Dict of {metric_id: values_array}
            max_corr_threshold: Maximum allowed correlation (default 0.85)

        Returns:
            (passed, redundancy_scores)
        """
        if not canonical_metrics:
            # No canonical metrics to compare against - pass by default
            return True, RedundancyScores(
                max_corr=0.0,
                mutual_info=0.0,
                nearest_metric_ids=[],
            )

        correlations = {}
        mutual_infos = {}

        for metric_id, canonical_values in canonical_metrics.items():
            # Ensure same length
            min_len = min(len(candidate_values), len(canonical_values))
            cand = candidate_values[:min_len]
            canon = canonical_values[:min_len]

            # Pearson correlation
            if len(cand) > 1 and np.std(cand) > 1e-10 and np.std(canon) > 1e-10:
                corr = np.corrcoef(cand, canon)[0, 1]
                correlations[metric_id] = abs(corr)
            else:
                correlations[metric_id] = 0.0

            # Mutual information (discretized approximation)
            mi = self._compute_mutual_information(cand, canon)
            mutual_infos[metric_id] = mi

        # Find maximum correlation
        max_corr = max(correlations.values()) if correlations else 0.0
        max_mi = max(mutual_infos.values()) if mutual_infos else 0.0

        # Find nearest metrics (top 3 by correlation)
        sorted_metrics = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
        nearest_metric_ids = [m[0] for m in sorted_metrics[:3]]

        redundancy_scores = RedundancyScores(
            max_corr=float(max_corr),
            mutual_info=float(max_mi),
            nearest_metric_ids=nearest_metric_ids,
        )

        # Pass if max correlation below threshold
        passed = max_corr < max_corr_threshold

        return passed, redundancy_scores

    def _compute_mutual_information(
        self, x: np.ndarray, y: np.ndarray, bins: int = 10
    ) -> float:
        """Compute discretized mutual information.

        Uses histogram-based approximation.

        Args:
            x, y: Input arrays
            bins: Number of bins for discretization

        Returns:
            Mutual information (nats)
        """
        # Discretize
        x_binned = np.digitize(x, bins=np.linspace(x.min(), x.max(), bins))
        y_binned = np.digitize(y, bins=np.linspace(y.min(), y.max(), bins))

        # Joint histogram
        joint_hist, _, _ = np.histogram2d(x_binned, y_binned, bins=bins)
        joint_prob = joint_hist / joint_hist.sum()

        # Marginals
        x_prob = joint_prob.sum(axis=1)
        y_prob = joint_prob.sum(axis=0)

        # Compute MI
        mi = 0.0
        for i in range(bins):
            for j in range(bins):
                if joint_prob[i, j] > 0 and x_prob[i] > 0 and y_prob[j] > 0:
                    mi += joint_prob[i, j] * np.log(
                        joint_prob[i, j] / (x_prob[i] * y_prob[j])
                    )

        return float(mi)

    def evaluate_rent_payment_gate(
        self,
        baseline_metrics: Dict[str, float],
        with_candidate_metrics: Dict[str, float],
    ) -> Tuple[bool, LiftMetrics]:
        """Gate 4: Rent Payment - measurable lift over baseline.

        Computes delta metrics:
        - forecast_error_delta (negative = improvement)
        - brier_delta (negative = improvement)
        - calibration_delta (positive = improvement)
        - misinfo_auc_delta (positive = improvement)
        - world_media_divergence_explained_delta (positive = improvement)

        Args:
            baseline_metrics: Performance without candidate metric
            with_candidate_metrics: Performance with candidate metric

        Returns:
            (passed, lift_metrics)
        """
        lift = LiftMetrics(
            forecast_error_delta=with_candidate_metrics.get("forecast_error", 0.0)
            - baseline_metrics.get("forecast_error", 0.0),
            brier_delta=with_candidate_metrics.get("brier_score", 0.0)
            - baseline_metrics.get("brier_score", 0.0),
            calibration_delta=with_candidate_metrics.get("calibration", 0.0)
            - baseline_metrics.get("calibration", 0.0),
            misinfo_auc_delta=with_candidate_metrics.get("misinfo_auc", 0.0)
            - baseline_metrics.get("misinfo_auc", 0.0),
            world_media_divergence_explained_delta=with_candidate_metrics.get(
                "divergence_explained", 0.0
            )
            - baseline_metrics.get("divergence_explained", 0.0),
        )

        # Check if meets thresholds
        passed = lift.meets_thresholds()

        return passed, lift

    def evaluate_ablation_gate(
        self,
        full_metrics: Dict[str, float],
        ablated_metrics: Dict[str, float],
        epsilon: float = 0.01,
    ) -> Tuple[bool, Dict[str, float]]:
        """Gate 5: Ablation - removal degrades performance.

        Run evaluation with metric enabled vs disabled.
        Metric passes if removing it degrades objective scores.

        Args:
            full_metrics: Performance with all metrics
            ablated_metrics: Performance with candidate metric removed
            epsilon: Minimum degradation threshold

        Returns:
            (passed, ablation_results)
        """
        # Compute degradation when candidate is removed
        # For error metrics (lower is better), ablated should be HIGHER (worse)
        # For quality metrics (higher is better), ablated should be LOWER (worse)

        forecast_error_degraded = (
            ablated_metrics.get("forecast_error", 0.0)
            - full_metrics.get("forecast_error", 0.0)
        )
        brier_degraded = (
            ablated_metrics.get("brier_score", 0.0)
            - full_metrics.get("brier_score", 0.0)
        )
        calibration_degraded = (
            full_metrics.get("calibration", 0.0)
            - ablated_metrics.get("calibration", 0.0)
        )
        auc_degraded = (
            full_metrics.get("misinfo_auc", 0.0)
            - ablated_metrics.get("misinfo_auc", 0.0)
        )

        ablation_results = {
            "forecast_error_degradation": float(forecast_error_degraded),
            "brier_degradation": float(brier_degraded),
            "calibration_degradation": float(calibration_degraded),
            "auc_degradation": float(auc_degraded),
        }

        # Pass if ANY metric shows degradation above epsilon
        passed = (
            forecast_error_degraded > epsilon
            or brier_degraded > epsilon
            or calibration_degraded > epsilon
            or auc_degraded > epsilon
        )

        return passed, ablation_results

    def evaluate_stabilization_gate(
        self,
        performance_history: List[Dict[str, float]],
        cycles_required: int = 5,
        variance_threshold: float = 0.05,
    ) -> Tuple[bool, StabilizationScores]:
        """Gate 6: Stabilization - consistent performance over N cycles.

        Checks:
        - Performance remains above thresholds for N consecutive cycles
        - Variance in performance is low (stable)
        - Drift tests passed (performance under noise perturbations)

        Args:
            performance_history: List of performance dicts over time
            cycles_required: Number of cycles required for stabilization
            variance_threshold: Maximum allowed performance variance

        Returns:
            (passed, stabilization_scores)
        """
        cycles_passed = len(performance_history)

        if cycles_passed < cycles_required:
            return False, StabilizationScores(
                cycles_required=cycles_required,
                cycles_passed=cycles_passed,
                drift_tests_passed=0,
                performance_variance=1.0,
            )

        # Compute variance of key metrics
        forecast_errors = [p.get("forecast_error", 0.0) for p in performance_history]
        brier_scores = [p.get("brier_score", 0.0) for p in performance_history]

        forecast_variance = float(np.var(forecast_errors)) if forecast_errors else 1.0
        brier_variance = float(np.var(brier_scores)) if brier_scores else 1.0

        performance_variance = max(forecast_variance, brier_variance)

        # Drift test: check if performance doesn't degrade significantly
        # (Simplified: check last 3 cycles vs first 3 cycles)
        drift_tests_passed = 0
        if cycles_passed >= 6:
            early_error = np.mean(forecast_errors[:3])
            late_error = np.mean(forecast_errors[-3:])

            # Pass if late error not significantly worse (within 10%)
            if late_error <= early_error * 1.1:
                drift_tests_passed = 1

        stabilization_scores = StabilizationScores(
            cycles_required=cycles_required,
            cycles_passed=cycles_passed,
            drift_tests_passed=drift_tests_passed,
            performance_variance=float(performance_variance),
        )

        # Pass if all conditions met
        passed = (
            cycles_passed >= cycles_required
            and performance_variance < variance_threshold
            and drift_tests_passed > 0
        )

        return passed, stabilization_scores

    def run_all_gates(
        self,
        candidate: CandidateMetric,
        candidate_values: np.ndarray,
        canonical_metrics: Dict[str, np.ndarray],
        baseline_metrics: Dict[str, float],
        with_candidate_metrics: Dict[str, float],
        full_metrics: Dict[str, float],
        ablated_metrics: Dict[str, float],
        performance_history: List[Dict[str, float]],
        seeds_used: List[int],
        outcome_ledger_slice_hashes: List[str],
    ) -> EvidenceBundle:
        """Run all promotion gates and generate evidence bundle.

        Args:
            candidate: Candidate metric
            candidate_values: Time series of candidate metric values
            canonical_metrics: Canonical metric values for redundancy check
            baseline_metrics: Performance without candidate
            with_candidate_metrics: Performance with candidate
            full_metrics: Performance with all metrics
            ablated_metrics: Performance with candidate removed
            performance_history: Historical performance for stabilization
            seeds_used: RNG seeds used in evaluation
            outcome_ledger_slice_hashes: Hashes of outcome ledger entries

        Returns:
            EvidenceBundle with all test results
        """
        # Gate 1: Provenance
        provenance_passed = self.evaluate_provenance_gate(candidate)

        # Gate 2: Falsifiability
        falsifiability_passed = self.evaluate_falsifiability_gate(candidate)

        # Gate 3: Non-Redundancy
        redundancy_passed, redundancy_scores = self.evaluate_redundancy_gate(
            candidate, candidate_values, canonical_metrics
        )

        # Gate 4: Rent Payment
        rent_passed, lift_metrics = self.evaluate_rent_payment_gate(
            baseline_metrics, with_candidate_metrics
        )

        # Gate 5: Ablation
        ablation_passed, ablation_results = self.evaluate_ablation_gate(
            full_metrics, ablated_metrics
        )

        # Gate 6: Stabilization
        stabilization_passed, stabilization_scores = self.evaluate_stabilization_gate(
            performance_history
        )

        # Compile test results
        test_results = TestResults(
            provenance_passed=provenance_passed,
            falsifiability_passed=falsifiability_passed,
            redundancy_passed=redundancy_passed,
            rent_payment_passed=rent_passed,
            ablation_passed=ablation_passed,
            stabilization_passed=stabilization_passed,
        )

        # Create evidence bundle
        evidence_bundle = EvidenceBundle(
            metric_id=candidate.provenance.metric_id,
            timestamp=candidate.last_updated,
            sim_version=self.sim_version,
            seeds_used=seeds_used,
            outcome_ledger_slice_hashes=outcome_ledger_slice_hashes,
            test_results=test_results,
            lift_metrics=lift_metrics,
            redundancy_scores=redundancy_scores,
            stabilization_scores=stabilization_scores,
            ablation_results=ablation_results,
        )

        return evidence_bundle


__all__ = ["MetricEvaluator"]
