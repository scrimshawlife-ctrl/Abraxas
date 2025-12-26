"""
Evidence Bundle System

Creates cryptographically sealed evidence bundles for metric promotion.
Evidence bundles are the ONLY basis for promoting metrics from shadow to canonical.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_canonical_json
from abraxas.metrics.thresholds import (
    MIN_ABLATION_DAMAGE,
    MIN_BRIER_DELTA,
    MIN_COMPOSITE_SCORE,
    MIN_DRIFT_SENSITIVITY,
    MIN_EVIDENCE_SAMPLES,
    MIN_FORECAST_ERROR_DELTA,
    MIN_MISINFO_AUC_DELTA,
    MIN_STABILITY_CYCLES,
    MAX_REDUNDANCY_CORR,
    MAX_STABILITY_VARIANCE,
    PROMOTION_REQUIRED_GATES,
)


class EvidenceBundle:
    """
    Creates and validates evidence bundles for metric promotion.

    Evidence bundles contain:
    - Hashes of all registry snapshots
    - Evaluation outputs (lift, redundancy, ablation, stabilization)
    - Thresholds used
    - Seeds used
    - Canonical hash of entire bundle
    """

    def __init__(self, evidence_dir: str | Path | None = None):
        """
        Initialize evidence bundle system.

        Args:
            evidence_dir: Directory to store evidence bundles (default: evidence/)
        """
        self.evidence_dir = Path(evidence_dir) if evidence_dir else Path("evidence")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def create_bundle(
        self,
        metric_id: str,
        candidate_spec: dict[str, Any],
        ledger_slice: list[dict[str, Any]],
        evaluation_results: dict[str, Any],
        registry_snapshots: dict[str, Any],
        seeds: list[int],
    ) -> dict[str, Any]:
        """
        Create evidence bundle for a candidate metric.

        Args:
            metric_id: Candidate metric ID
            candidate_spec: Full metric specification
            ledger_slice: Outcome ledger entries used
            evaluation_results: Outputs from evaluation (lift, ablation, etc.)
            registry_snapshots: Hashes of metrics/simvars/runes registries
            seeds: Random seeds used for evaluation

        Returns:
            Evidence bundle dict
        """
        # Hash all inputs
        candidate_hash = hash_canonical_json(candidate_spec)
        ledger_hash = hash_canonical_json(ledger_slice)
        registry_hash = hash_canonical_json(registry_snapshots)

        # Extract evaluation metrics
        lift_metrics = evaluation_results.get("lift", {})
        redundancy_metrics = evaluation_results.get("redundancy", {})
        ablation_results = evaluation_results.get("ablation", {})
        stability_results = evaluation_results.get("stability", {})

        # Gate evaluation
        gates_passed = self._evaluate_gates(
            lift_metrics=lift_metrics,
            redundancy_metrics=redundancy_metrics,
            ablation_results=ablation_results,
            stability_results=stability_results,
        )

        # Compute composite score
        composite_score = self._compute_composite_score(evaluation_results)

        # Build bundle
        bundle = {
            "metric_id": metric_id,
            "bundle_id": f"{metric_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "hashes": {
                "candidate_spec": candidate_hash,
                "ledger_slice": ledger_hash,
                "registry_snapshots": registry_hash,
            },
            "evaluation_outputs": {
                "lift_metrics": lift_metrics,
                "redundancy_metrics": redundancy_metrics,
                "ablation_results": ablation_results,
                "stability_results": stability_results,
            },
            "thresholds_used": {
                "MAX_REDUNDANCY_CORR": MAX_REDUNDANCY_CORR,
                "MIN_FORECAST_ERROR_DELTA": MIN_FORECAST_ERROR_DELTA,
                "MIN_BRIER_DELTA": MIN_BRIER_DELTA,
                "MIN_MISINFO_AUC_DELTA": MIN_MISINFO_AUC_DELTA,
                "MIN_ABLATION_DAMAGE": MIN_ABLATION_DAMAGE,
                "MIN_STABILITY_CYCLES": MIN_STABILITY_CYCLES,
                "MAX_STABILITY_VARIANCE": MAX_STABILITY_VARIANCE,
                "MIN_DRIFT_SENSITIVITY": MIN_DRIFT_SENSITIVITY,
                "MIN_COMPOSITE_SCORE": MIN_COMPOSITE_SCORE,
            },
            "seeds_used": seeds,
            "gates_passed": gates_passed,
            "composite_score": composite_score,
            "promotion_eligible": all(
                gates_passed.get(gate, False) for gate in PROMOTION_REQUIRED_GATES
            )
            and composite_score >= MIN_COMPOSITE_SCORE,
            "sample_size": len(ledger_slice),
        }

        # Hash entire bundle (canonical)
        bundle["bundle_hash"] = hash_canonical_json(bundle)

        return bundle

    def _evaluate_gates(
        self,
        lift_metrics: dict[str, float],
        redundancy_metrics: dict[str, float],
        ablation_results: dict[str, float],
        stability_results: dict[str, Any],
    ) -> dict[str, bool]:
        """
        Evaluate promotion gates.

        Args:
            lift_metrics: Forecast improvement metrics
            redundancy_metrics: Redundancy analysis outputs
            ablation_results: Ablation test outputs
            stability_results: Stabilization outputs

        Returns:
            Dict of gate_name -> passed (bool)
        """
        gates = {}

        # Non-redundancy gate
        max_corr = redundancy_metrics.get("max_correlation", 1.0)
        gates["non_redundant"] = max_corr < MAX_REDUNDANCY_CORR

        # Forecast lift gate (any meaningful improvement)
        forecast_delta = lift_metrics.get("mae_delta", 0.0)
        brier_delta = lift_metrics.get("brier_delta", 0.0)
        misinfo_auc_delta = lift_metrics.get("misinfo_auc_delta", 0.0)

        gates["forecast_lift"] = (
            forecast_delta >= MIN_FORECAST_ERROR_DELTA
            or brier_delta >= MIN_BRIER_DELTA
            or misinfo_auc_delta >= MIN_MISINFO_AUC_DELTA
        )

        # Ablation proof gate
        ablation_damage = ablation_results.get("performance_drop", 0.0)
        gates["ablation_proof"] = ablation_damage >= MIN_ABLATION_DAMAGE

        # Stability gate
        stable_cycles = stability_results.get("stable_cycles", 0)
        variance_coeff = stability_results.get("coefficient_variation", 1.0)
        gates["stability_verified"] = (
            stable_cycles >= MIN_STABILITY_CYCLES
            and variance_coeff <= MAX_STABILITY_VARIANCE
        )

        # Drift robustness gate
        drift_detection_rate = stability_results.get("drift_detection_rate", 0.0)
        gates["drift_robust"] = drift_detection_rate >= MIN_DRIFT_SENSITIVITY

        return gates

    def _compute_composite_score(self, evaluation_results: dict[str, Any]) -> float:
        """
        Compute weighted composite score across all evaluation dimensions.

        Args:
            evaluation_results: Full evaluation outputs

        Returns:
            Composite score in [0, 1]
        """
        lift = evaluation_results.get("lift", {})
        redundancy = evaluation_results.get("redundancy", {})
        ablation = evaluation_results.get("ablation", {})
        stability = evaluation_results.get("stability", {})

        # Normalize each dimension to [0, 1]
        lift_score = min(
            1.0,
            max(
                lift.get("mae_delta", 0.0) / 0.10,  # 10% improvement = 1.0
                lift.get("brier_delta", 0.0) / 0.05,
                lift.get("misinfo_auc_delta", 0.0) / 0.10,
            ),
        )

        redundancy_score = max(
            0.0, 1.0 - redundancy.get("max_correlation", 0.0)
        )  # Lower corr = better

        ablation_score = min(
            1.0, ablation.get("performance_drop", 0.0) / 0.20
        )  # 20% drop = 1.0

        stability_score = min(
            1.0,
            (stability.get("stable_cycles", 0) / MIN_STABILITY_CYCLES)
            * (1.0 - stability.get("coefficient_variation", 1.0)),
        )

        # Weighted average (can be tuned)
        weights = {
            "lift": 0.35,
            "redundancy": 0.20,
            "ablation": 0.25,
            "stability": 0.20,
        }

        composite = (
            weights["lift"] * lift_score
            + weights["redundancy"] * redundancy_score
            + weights["ablation"] * ablation_score
            + weights["stability"] * stability_score
        )

        return composite

    def write_bundle(self, bundle: dict[str, Any]) -> Path:
        """
        Write evidence bundle to disk.

        Args:
            bundle: Evidence bundle dict

        Returns:
            Path to written bundle file
        """
        metric_id = bundle["metric_id"]
        bundle_id = bundle["bundle_id"]

        # Create metric-specific directory
        metric_dir = self.evidence_dir / metric_id
        metric_dir.mkdir(parents=True, exist_ok=True)

        # Write bundle
        bundle_path = metric_dir / f"{bundle_id}.json"
        with open(bundle_path, "w") as f:
            json.dump(bundle, f, indent=2, sort_keys=True, default=str)

        return bundle_path

    def load_bundle(self, metric_id: str, bundle_id: str) -> dict[str, Any]:
        """
        Load evidence bundle from disk.

        Args:
            metric_id: Metric ID
            bundle_id: Bundle ID

        Returns:
            Evidence bundle dict
        """
        bundle_path = self.evidence_dir / metric_id / f"{bundle_id}.json"
        if not bundle_path.exists():
            raise FileNotFoundError(f"Evidence bundle not found: {bundle_path}")

        with open(bundle_path, "r") as f:
            return json.load(f)

    def verify_bundle_integrity(self, bundle: dict[str, Any]) -> bool:
        """
        Verify bundle hash integrity.

        Args:
            bundle: Evidence bundle dict

        Returns:
            True if bundle hash matches computed hash
        """
        bundle_copy = bundle.copy()
        claimed_hash = bundle_copy.pop("bundle_hash", None)

        if claimed_hash is None:
            return False

        computed_hash = hash_canonical_json(bundle_copy)
        return claimed_hash == computed_hash

    def get_promotion_ready_metrics(self) -> list[dict[str, Any]]:
        """
        Scan evidence directory for promotion-eligible bundles.

        Returns:
            List of (metric_id, bundle_id, bundle_path) for eligible metrics
        """
        eligible = []

        for metric_dir in self.evidence_dir.iterdir():
            if not metric_dir.is_dir():
                continue

            metric_id = metric_dir.name
            for bundle_file in metric_dir.glob("*.json"):
                try:
                    with open(bundle_file, "r") as f:
                        bundle = json.load(f)

                    if bundle.get("promotion_eligible", False):
                        eligible.append(
                            {
                                "metric_id": metric_id,
                                "bundle_id": bundle["bundle_id"],
                                "bundle_path": str(bundle_file),
                                "composite_score": bundle.get("composite_score", 0.0),
                                "created_at": bundle.get("created_at"),
                            }
                        )
                except (json.JSONDecodeError, KeyError):
                    continue

        # Sort by score descending
        eligible.sort(key=lambda x: x["composite_score"], reverse=True)

        return eligible
