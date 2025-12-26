"""
Metric Emergence Module

Proposes candidate metrics from unexplained residuals, drift signals,
and anomaly clusters in the Outcome Ledger.

CRITICAL: This module PROPOSES only. It does NOT promote or modify canonical metrics.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_canonical_json


class HypothesisType:
    """Enumeration of metric hypothesis types."""

    RESIDUAL_EXPLAINER = "residual_explainer"
    REDUNDANCY_SPLITTER = "redundancy_splitter"
    MANIPULATION_DETECTOR = "manipulation_detector"
    COUPLING_BRIDGE = "coupling_bridge"
    TEMPORAL_CORRELATE = "temporal_correlate"


class MetricStatus:
    """Lifecycle status for candidate metrics."""

    PROPOSED = "PROPOSED"
    SHADOW = "SHADOW"
    SCORED = "SCORED"
    STABILIZING = "STABILIZING"
    READY = "READY"
    REJECTED = "REJECTED"
    MERGED = "MERGED"


class MetricEmergence:
    """
    Proposes candidate metrics from ledger analysis.

    Does NOT modify canonical metrics registry.
    Writes proposals to registry/metrics_candidate.json
    """

    def __init__(
        self,
        ledger_path: str | Path | None = None,
        canonical_metrics_path: str | Path | None = None,
        runes_registry_path: str | Path | None = None,
        output_path: str | Path | None = None,
    ):
        """
        Initialize emergence module.

        Args:
            ledger_path: Path to outcome ledger
            canonical_metrics_path: Path to canonical metrics registry
            runes_registry_path: Path to rune bindings registry
            output_path: Path to write candidate metrics (default: registry/metrics_candidate.json)
        """
        self.ledger_path = Path(ledger_path) if ledger_path else Path(".aal/ledger/outcomes.jsonl")
        self.canonical_metrics_path = (
            Path(canonical_metrics_path)
            if canonical_metrics_path
            else Path("registry/metrics.json")
        )
        self.runes_registry_path = (
            Path(runes_registry_path)
            if runes_registry_path
            else Path("abraxas/runes/registry.json")
        )
        self.output_path = (
            Path(output_path) if output_path else Path("registry/metrics_candidate.json")
        )

    def load_ledger_slice(
        self, hash_range: tuple[str, str] | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Load outcome ledger slice.

        Args:
            hash_range: (start_hash, end_hash) for deterministic slicing
            limit: Maximum number of entries to load

        Returns:
            List of ledger entries
        """
        entries = []
        if not self.ledger_path.exists():
            return entries

        with open(self.ledger_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

        # Apply hash range filter if specified
        if hash_range:
            start_hash, end_hash = hash_range
            entries = [
                e
                for e in entries
                if start_hash <= e.get("ledger_sha256", "") <= end_hash
            ]

        # Apply limit
        if limit:
            entries = entries[:limit]

        return entries

    def load_canonical_metrics(self) -> dict[str, Any]:
        """Load canonical metrics registry."""
        if not self.canonical_metrics_path.exists():
            return {"metrics": [], "version": "0.0.0"}

        with open(self.canonical_metrics_path, "r") as f:
            return json.load(f)

    def load_rune_registry(self) -> dict[str, Any]:
        """Load rune bindings registry."""
        if not self.runes_registry_path.exists():
            return {"runes": [], "version": "0.0.0"}

        with open(self.runes_registry_path, "r") as f:
            return json.load(f)

    def analyze_residuals(
        self, ledger_entries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Detect unexplained residuals that suggest missing metrics.

        Args:
            ledger_entries: Outcome ledger slice

        Returns:
            List of residual patterns with metadata
        """
        residuals = []

        # Group entries by metric_id to detect variance patterns
        metric_variances: dict[str, list[float]] = {}
        for entry in ledger_entries:
            canonical_metrics = entry.get("canonical_metrics", {})
            for metric_id, value in canonical_metrics.items():
                if isinstance(value, (int, float)):
                    if metric_id not in metric_variances:
                        metric_variances[metric_id] = []
                    metric_variances[metric_id].append(float(value))

        # Detect high-variance metrics (potential explainability gap)
        for metric_id, values in metric_variances.items():
            if len(values) < 10:
                continue

            mean_val = sum(values) / len(values)
            variance = sum((v - mean_val) ** 2 for v in values) / len(values)
            std_dev = variance**0.5

            # High coefficient of variation suggests unexplained dynamics
            if mean_val != 0:
                cv = std_dev / abs(mean_val)
                if cv > 0.30:  # >30% coefficient of variation
                    residuals.append(
                        {
                            "pattern_type": "high_variance",
                            "source_metric": metric_id,
                            "coefficient_variation": cv,
                            "sample_size": len(values),
                            "mean": mean_val,
                            "std_dev": std_dev,
                        }
                    )

        return residuals

    def analyze_divergence(
        self, ledger_entries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Detect divergence between correlated metrics.

        Args:
            ledger_entries: Outcome ledger slice

        Returns:
            List of divergence patterns
        """
        divergences = []

        # Extract time-series for each metric
        metric_series: dict[str, list[tuple[datetime, float]]] = {}
        for entry in ledger_entries:
            ts_str = entry.get("timestamp")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue

            canonical_metrics = entry.get("canonical_metrics", {})
            for metric_id, value in canonical_metrics.items():
                if isinstance(value, (int, float)):
                    if metric_id not in metric_series:
                        metric_series[metric_id] = []
                    metric_series[metric_id].append((ts, float(value)))

        # Look for metrics with sudden divergence (correlation breakdown)
        # Simplified: check if two high-correlation metrics show rapid decorrelation
        metric_ids = list(metric_series.keys())
        for i, metric_a in enumerate(metric_ids):
            for metric_b in metric_ids[i + 1 :]:
                series_a = metric_series[metric_a]
                series_b = metric_series[metric_b]

                if len(series_a) < 20 or len(series_b) < 20:
                    continue

                # Align by timestamp (simple intersection)
                common_ts = set(ts for ts, _ in series_a) & set(ts for ts, _ in series_b)
                if len(common_ts) < 20:
                    continue

                vals_a = [v for ts, v in series_a if ts in common_ts]
                vals_b = [v for ts, v in series_b if ts in common_ts]

                # Compute correlation (Pearson)
                n = len(vals_a)
                mean_a = sum(vals_a) / n
                mean_b = sum(vals_b) / n
                cov = sum((vals_a[k] - mean_a) * (vals_b[k] - mean_b) for k in range(n)) / n
                std_a = (sum((v - mean_a) ** 2 for v in vals_a) / n) ** 0.5
                std_b = (sum((v - mean_b) ** 2 for v in vals_b) / n) ** 0.5

                if std_a == 0 or std_b == 0:
                    continue

                corr = cov / (std_a * std_b)

                # If high correlation but metrics diverge in tail, flag for bridge metric
                if corr > 0.70:
                    # Check tail divergence (last 20% of samples)
                    tail_start = int(0.8 * n)
                    tail_vals_a = vals_a[tail_start:]
                    tail_vals_b = vals_b[tail_start:]

                    tail_mean_a = sum(tail_vals_a) / len(tail_vals_a)
                    tail_mean_b = sum(tail_vals_b) / len(tail_vals_b)

                    # Normalized divergence
                    div_a = abs(tail_mean_a - mean_a) / (std_a + 1e-9)
                    div_b = abs(tail_mean_b - mean_b) / (std_b + 1e-9)

                    if abs(div_a - div_b) > 1.0:  # Divergent tails
                        divergences.append(
                            {
                                "pattern_type": "correlation_breakdown",
                                "metric_a": metric_a,
                                "metric_b": metric_b,
                                "overall_correlation": corr,
                                "tail_divergence": abs(div_a - div_b),
                                "sample_size": n,
                            }
                        )

        return divergences

    def propose_candidates(
        self,
        residuals: list[dict[str, Any]],
        divergences: list[dict[str, Any]],
        canonical_metrics: dict[str, Any],
        rune_registry: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Generate candidate metric specifications from patterns.

        Args:
            residuals: Residual patterns
            divergences: Divergence patterns
            canonical_metrics: Current canonical metrics
            rune_registry: Current rune bindings

        Returns:
            List of candidate metric specs
        """
        candidates = []

        # Generate candidates from residuals
        for residual in residuals:
            source_metric = residual["source_metric"]
            candidate_id = f"metric_res_{hash_canonical_json(residual)[:12]}"

            candidate = {
                "metric_id": candidate_id,
                "hypothesis_type": HypothesisType.RESIDUAL_EXPLAINER,
                "description": f"Explains high variance in {source_metric} (CV={residual['coefficient_variation']:.2f})",
                "proposed_inputs": [source_metric, "context_vector", "temporal_window"],
                "proposed_simvar_targets": [f"{source_metric}_residual", "explained_variance"],
                "proposed_rune_contract": {
                    "inputs": {"metric": source_metric, "window_size": "int"},
                    "outputs": {"residual": "float", "explained_ratio": "float"},
                    "constraints": ["residual >= 0", "explained_ratio in [0, 1]"],
                },
                "falsification_criteria": [
                    f"Reduction in {source_metric} variance by <10%",
                    "Correlation with existing metrics >0.85",
                    "Fails to generalize across 3+ simulation runs",
                ],
                "evaluation_window": {"min_cycles": 50, "min_samples": 100},
                "status": MetricStatus.PROPOSED,
                "provenance": {
                    "discovered_from": "residual_analysis",
                    "source_pattern": residual,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            candidates.append(candidate)

        # Generate candidates from divergences
        for divergence in divergences:
            metric_a = divergence["metric_a"]
            metric_b = divergence["metric_b"]
            candidate_id = f"metric_bridge_{hash_canonical_json(divergence)[:12]}"

            candidate = {
                "metric_id": candidate_id,
                "hypothesis_type": HypothesisType.COUPLING_BRIDGE,
                "description": f"Bridges divergence between {metric_a} and {metric_b}",
                "proposed_inputs": [metric_a, metric_b, "phase_context"],
                "proposed_simvar_targets": [
                    f"coupling_{metric_a}_{metric_b}",
                    "phase_coherence",
                ],
                "proposed_rune_contract": {
                    "inputs": {"metric_a": metric_a, "metric_b": metric_b},
                    "outputs": {"coupling_strength": "float", "phase_delta": "float"},
                    "constraints": ["coupling_strength in [0, 1]", "phase_delta in [-π, π]"],
                },
                "falsification_criteria": [
                    "Coupling metric correlates >0.90 with either input",
                    "Fails to predict divergence events",
                    "Unstable across perturbations",
                ],
                "evaluation_window": {"min_cycles": 100, "min_samples": 200},
                "status": MetricStatus.PROPOSED,
                "provenance": {
                    "discovered_from": "divergence_analysis",
                    "source_pattern": divergence,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            candidates.append(candidate)

        return candidates

    def run_emergence(
        self, hash_range: tuple[str, str] | None = None, limit: int | None = 1000
    ) -> list[dict[str, Any]]:
        """
        Execute full emergence pipeline.

        Args:
            hash_range: Optional ledger slice by hash range
            limit: Maximum ledger entries to analyze

        Returns:
            List of proposed candidate metrics
        """
        # Load inputs
        ledger_entries = self.load_ledger_slice(hash_range=hash_range, limit=limit)
        canonical_metrics = self.load_canonical_metrics()
        rune_registry = self.load_rune_registry()

        # Analyze patterns
        residuals = self.analyze_residuals(ledger_entries)
        divergences = self.analyze_divergence(ledger_entries)

        # Propose candidates
        candidates = self.propose_candidates(
            residuals=residuals,
            divergences=divergences,
            canonical_metrics=canonical_metrics,
            rune_registry=rune_registry,
        )

        return candidates

    def write_candidates(self, candidates: list[dict[str, Any]]) -> None:
        """
        Write candidates to output registry.

        DOES NOT modify canonical metrics.

        Args:
            candidates: List of candidate metric specs
        """
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing candidates
        existing_candidates = []
        if self.output_path.exists():
            with open(self.output_path, "r") as f:
                data = json.load(f)
                existing_candidates = data.get("candidates", [])

        # Merge (deduplicate by metric_id)
        existing_ids = {c["metric_id"] for c in existing_candidates}
        new_candidates = [c for c in candidates if c["metric_id"] not in existing_ids]

        all_candidates = existing_candidates + new_candidates

        # Write output
        output = {
            "version": "1.0.0",
            "generated": datetime.now(timezone.utc).isoformat(),
            "registry_type": "metric_candidates",
            "candidates": all_candidates,
        }

        with open(self.output_path, "w") as f:
            json.dump(output, f, indent=2, sort_keys=True, default=str)

    def propose_and_write(
        self, hash_range: tuple[str, str] | None = None, limit: int | None = 1000
    ) -> list[dict[str, Any]]:
        """
        Run emergence and write candidates in one step.

        Args:
            hash_range: Optional ledger slice
            limit: Max ledger entries

        Returns:
            Proposed candidates
        """
        candidates = self.run_emergence(hash_range=hash_range, limit=limit)
        self.write_candidates(candidates)
        return candidates
