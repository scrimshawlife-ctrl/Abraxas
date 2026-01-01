"""Metric Governance: Candidate-First Lifecycle with Promotion Gates

NON-NEGOTIABLE LAWS:
1. Metrics are Contracts, not Ideas
2. Candidate-First Lifecycle (no direct canonical entry)
3. Promotion Requires Evidence Bundle
4. Complexity Pays Rent (measurable lift + ablation survival)
5. Stabilization Window Required (N cycles with consistent performance)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.metrics.hashutil import compute_chain_signature, hash_json


class CandidateStatus(Enum):
    """Lifecycle status for candidate metrics."""
    PROPOSED = "PROPOSED"          # Initial submission
    SHADOW = "SHADOW"              # Running in shadow mode (observing only)
    SCORED = "SCORED"              # Initial evaluation complete
    STABILIZING = "STABILIZING"    # In stabilization window
    READY = "READY"                # Passed all gates, awaiting promotion
    PROMOTED = "PROMOTED"          # Moved to canonical registry
    REJECTED = "REJECTED"          # Failed gates
    MERGED = "MERGED"              # Merged with existing canonical metric


class PromotionDecision(Enum):
    """Outcome of promotion evaluation."""
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    MERGED = "MERGED"


@dataclass(frozen=True)
class FalsifiabilityCriteria:
    """Falsifiability requirements for candidate metric."""
    predictions_influenced: List[str]  # Variable IDs this metric influences
    disconfirmation_criteria: Dict[str, Any]  # What would reduce confidence
    evaluation_window: int  # Timesteps for evaluation

    def to_dict(self) -> Dict:
        return {
            "predictions_influenced": self.predictions_influenced,
            "disconfirmation_criteria": self.disconfirmation_criteria,
            "evaluation_window": self.evaluation_window,
        }

    @staticmethod
    def from_dict(data: Dict) -> FalsifiabilityCriteria:
        return FalsifiabilityCriteria(
            predictions_influenced=data["predictions_influenced"],
            disconfirmation_criteria=data["disconfirmation_criteria"],
            evaluation_window=data["evaluation_window"],
        )


@dataclass(frozen=True)
class ProvenanceMeta:
    """Provenance metadata for candidate metric."""
    metric_id: str
    description: str
    units: str
    valid_range: Dict[str, float]
    dependencies: List[str]
    compute_fn: str  # Reference to computation function or formula
    input_sources: List[Dict[str, str]]  # [{source, hash}, ...]

    def to_dict(self) -> Dict:
        return {
            "metric_id": self.metric_id,
            "description": self.description,
            "units": self.units,
            "valid_range": self.valid_range,
            "dependencies": self.dependencies,
            "compute_fn": self.compute_fn,
            "input_sources": self.input_sources,
        }

    @staticmethod
    def from_dict(data: Dict) -> ProvenanceMeta:
        return ProvenanceMeta(
            metric_id=data["metric_id"],
            description=data["description"],
            units=data["units"],
            valid_range=data["valid_range"],
            dependencies=data["dependencies"],
            compute_fn=data["compute_fn"],
            input_sources=data["input_sources"],
        )


@dataclass
class CandidateMetric:
    """Candidate metric definition.

    All emergent metrics start here and must earn promotion.
    """
    provenance: ProvenanceMeta
    falsifiability: FalsifiabilityCriteria
    status: CandidateStatus
    required_rune_bindings: List[str]  # Rune IDs this metric requires
    target_sim_variables: List[str]  # Variable IDs this metric targets
    version: str = "0.1.0"
    created: Optional[str] = None
    last_updated: Optional[str] = None
    evaluation_history: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        if self.created is None:
            self.created = datetime.utcnow().isoformat() + "Z"
        if self.last_updated is None:
            self.last_updated = self.created

    def to_dict(self) -> Dict:
        return {
            "provenance": self.provenance.to_dict(),
            "falsifiability": self.falsifiability.to_dict(),
            "status": self.status.value,
            "required_rune_bindings": self.required_rune_bindings,
            "target_sim_variables": self.target_sim_variables,
            "version": self.version,
            "created": self.created,
            "last_updated": self.last_updated,
            "evaluation_history": self.evaluation_history,
        }

    @staticmethod
    def from_dict(data: Dict) -> CandidateMetric:
        return CandidateMetric(
            provenance=ProvenanceMeta.from_dict(data["provenance"]),
            falsifiability=FalsifiabilityCriteria.from_dict(data["falsifiability"]),
            status=CandidateStatus(data["status"]),
            required_rune_bindings=data["required_rune_bindings"],
            target_sim_variables=data["target_sim_variables"],
            version=data["version"],
            created=data.get("created"),
            last_updated=data.get("last_updated"),
            evaluation_history=data.get("evaluation_history", []),
        )

    def update_status(self, new_status: CandidateStatus):
        """Update status and timestamp."""
        self.status = new_status
        self.last_updated = datetime.utcnow().isoformat() + "Z"

    def add_evaluation(self, evaluation_result: Dict):
        """Add evaluation result to history."""
        self.evaluation_history.append(evaluation_result)
        self.last_updated = datetime.utcnow().isoformat() + "Z"


@dataclass
class RedundancyScores:
    """Redundancy metrics against canonical metrics."""
    max_corr: float  # Maximum Pearson correlation with any canonical metric
    mutual_info: float  # Maximum mutual information
    nearest_metric_ids: List[str]  # IDs of most similar canonical metrics

    def to_dict(self) -> Dict:
        return {
            "max_corr": self.max_corr,
            "mutual_info": self.mutual_info,
            "nearest_metric_ids": self.nearest_metric_ids,
        }


@dataclass
class LiftMetrics:
    """Lift metrics: improvement over baseline."""
    forecast_error_delta: float  # Negative = improvement
    brier_delta: float  # Negative = improvement
    calibration_delta: float  # Positive = improvement
    misinfo_auc_delta: float  # Positive = improvement
    world_media_divergence_explained_delta: float  # Positive = improvement

    def to_dict(self) -> Dict:
        return {
            "forecast_error_delta": self.forecast_error_delta,
            "brier_delta": self.brier_delta,
            "calibration_delta": self.calibration_delta,
            "misinfo_auc_delta": self.misinfo_auc_delta,
            "world_media_divergence_explained_delta": self.world_media_divergence_explained_delta,
        }

    def meets_thresholds(self) -> bool:
        """Check if lift meets minimum thresholds.

        Thresholds (default, conservative):
        - forecast_error_delta <= -0.02 (2% error reduction)
        - OR brier_delta <= -0.01 (1% Brier reduction)
        - OR calibration_delta >= 0.05 (5% calibration improvement)
        - OR misinfo_auc_delta >= 0.03 (3% AUC improvement)
        - OR world_media_divergence_explained_delta >= 0.05 (5% variance explained)
        """
        FORECAST_ERROR_THRESHOLD = -0.02
        BRIER_THRESHOLD = -0.01
        CALIBRATION_THRESHOLD = 0.05
        AUC_THRESHOLD = 0.03
        DIVERGENCE_THRESHOLD = 0.05

        return (
            self.forecast_error_delta <= FORECAST_ERROR_THRESHOLD
            or self.brier_delta <= BRIER_THRESHOLD
            or self.calibration_delta >= CALIBRATION_THRESHOLD
            or self.misinfo_auc_delta >= AUC_THRESHOLD
            or self.world_media_divergence_explained_delta >= DIVERGENCE_THRESHOLD
        )


@dataclass
class StabilizationScores:
    """Stabilization window performance."""
    cycles_required: int
    cycles_passed: int
    drift_tests_passed: int
    performance_variance: float  # Lower = more stable

    def to_dict(self) -> Dict:
        return {
            "cycles_required": self.cycles_required,
            "cycles_passed": self.cycles_passed,
            "drift_tests_passed": self.drift_tests_passed,
            "performance_variance": self.performance_variance,
        }

    def is_stable(self) -> bool:
        """Check if metric is stable."""
        return self.cycles_passed >= self.cycles_required and self.drift_tests_passed > 0


@dataclass
class TestResults:
    """Results from all promotion gates."""
    provenance_passed: bool
    falsifiability_passed: bool
    redundancy_passed: bool
    rent_payment_passed: bool
    ablation_passed: bool
    stabilization_passed: bool

    def to_dict(self) -> Dict:
        return {
            "provenance": self.provenance_passed,
            "falsifiability": self.falsifiability_passed,
            "redundancy": self.redundancy_passed,
            "rent_payment": self.rent_payment_passed,
            "ablation": self.ablation_passed,
            "stabilization": self.stabilization_passed,
        }

    def all_passed(self) -> bool:
        """Check if all gates passed."""
        return all([
            self.provenance_passed,
            self.falsifiability_passed,
            self.redundancy_passed,
            self.rent_payment_passed,
            self.ablation_passed,
            self.stabilization_passed,
        ])


@dataclass
class EvidenceBundle:
    """Evidence bundle for promotion decision.

    CRITICAL: Promotion is forbidden unless this exists and hash matches ledger.
    """
    metric_id: str
    timestamp: str
    sim_version: str
    seeds_used: List[int]
    outcome_ledger_slice_hashes: List[str]  # References to outcome ledger entries
    test_results: TestResults
    lift_metrics: LiftMetrics
    redundancy_scores: RedundancyScores
    stabilization_scores: StabilizationScores
    ablation_results: Dict[str, float]  # {metric_id: performance_with_removed}

    def to_dict(self) -> Dict:
        return {
            "metric_id": self.metric_id,
            "timestamp": self.timestamp,
            "sim_version": self.sim_version,
            "seeds_used": self.seeds_used,
            "outcome_ledger_slice_hashes": self.outcome_ledger_slice_hashes,
            "test_results": self.test_results.to_dict(),
            "lift_metrics": self.lift_metrics.to_dict(),
            "redundancy_scores": self.redundancy_scores.to_dict(),
            "stabilization_scores": self.stabilization_scores.to_dict(),
            "ablation_results": self.ablation_results,
        }

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of evidence bundle."""
        return hash_json(self.to_dict())


@dataclass
class PromotionLedgerEntry:
    """Single entry in metric promotion ledger (append-only)."""
    timestamp: str
    metric_id: str
    candidate_version: str
    sim_version: str
    seeds_used: List[int]
    evidence_bundle_hash: str
    tests_run: Dict[str, bool]
    lift_metrics: Dict[str, float]
    redundancy_scores: Dict[str, Any]
    stabilization: Dict[str, Any]
    decision: PromotionDecision
    rationale: str  # Short, non-poetic explanation
    signature: str  # sha256(prev_hash + entry_json_c14n)
    prev_hash: str = "0" * 64  # Genesis entry has all zeros

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "metric_id": self.metric_id,
            "candidate_version": self.candidate_version,
            "sim_version": self.sim_version,
            "seeds_used": self.seeds_used,
            "evidence_bundle_hash": self.evidence_bundle_hash,
            "tests_run": self.tests_run,
            "lift_metrics": self.lift_metrics,
            "redundancy_scores": self.redundancy_scores,
            "stabilization": self.stabilization,
            "decision": self.decision.value,
            "rationale": self.rationale,
            "prev_hash": self.prev_hash,
            "signature": self.signature,
        }

    @staticmethod
    def from_dict(data: Dict) -> PromotionLedgerEntry:
        return PromotionLedgerEntry(
            timestamp=data["timestamp"],
            metric_id=data["metric_id"],
            candidate_version=data["candidate_version"],
            sim_version=data["sim_version"],
            seeds_used=data["seeds_used"],
            evidence_bundle_hash=data["evidence_bundle_hash"],
            tests_run=data["tests_run"],
            lift_metrics=data["lift_metrics"],
            redundancy_scores=data["redundancy_scores"],
            stabilization=data["stabilization"],
            decision=PromotionDecision(data["decision"]),
            rationale=data["rationale"],
            prev_hash=data["prev_hash"],
            signature=data["signature"],
        )

    @staticmethod
    def create_entry(
        metric_id: str,
        candidate_version: str,
        sim_version: str,
        evidence_bundle: EvidenceBundle,
        decision: PromotionDecision,
        rationale: str,
        prev_hash: str = "0" * 64,
    ) -> PromotionLedgerEntry:
        """Create new ledger entry with computed signature."""
        entry_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metric_id": metric_id,
            "candidate_version": candidate_version,
            "sim_version": sim_version,
            "seeds_used": evidence_bundle.seeds_used,
            "evidence_bundle_hash": evidence_bundle.compute_hash(),
            "tests_run": evidence_bundle.test_results.to_dict(),
            "lift_metrics": evidence_bundle.lift_metrics.to_dict(),
            "redundancy_scores": evidence_bundle.redundancy_scores.to_dict(),
            "stabilization": evidence_bundle.stabilization_scores.to_dict(),
            "decision": decision.value,
            "rationale": rationale,
            "prev_hash": prev_hash,
        }

        signature = compute_chain_signature(entry_data, prev_hash)

        return PromotionLedgerEntry(
            timestamp=entry_data["timestamp"],
            metric_id=entry_data["metric_id"],
            candidate_version=entry_data["candidate_version"],
            sim_version=entry_data["sim_version"],
            seeds_used=entry_data["seeds_used"],
            evidence_bundle_hash=entry_data["evidence_bundle_hash"],
            tests_run=entry_data["tests_run"],
            lift_metrics=entry_data["lift_metrics"],
            redundancy_scores=entry_data["redundancy_scores"],
            stabilization=entry_data["stabilization"],
            decision=PromotionDecision(entry_data["decision"]),
            rationale=entry_data["rationale"],
            prev_hash=prev_hash,
            signature=signature,
        )


__all__ = [
    "CandidateStatus",
    "PromotionDecision",
    "FalsifiabilityCriteria",
    "ProvenanceMeta",
    "CandidateMetric",
    "RedundancyScores",
    "LiftMetrics",
    "StabilizationScores",
    "TestResults",
    "EvidenceBundle",
    "PromotionLedgerEntry",
]
