"""Trutina Evidence Provider for Abraxas evidence system."""

from __future__ import annotations

import random
import math
from typing import Any, Dict, List, Optional

from abraxas.evidence.contract import (
    EvidenceEnvelope, EvidenceType, CandidateOutput
)
from abraxas.evidence.provider import EvidenceProvider
from abraxas.evidence import (
    compute_atomic_brier,
    compute_brier_series,
    to_brier_score_packet,
    to_brier_ledger_entry,
    compute_ledger_hash,
    compute_score_hash,
)


class TrutinaEvidenceProvider(EvidenceProvider):
    """Trutina evidence provider — Brier calibration and scoring."""

    @property
    def engine_name(self) -> str:
        return "trutina"

    @property
    def engine_version(self) -> str:
        return "trutina.brier.v1"

    @property
    def supported_evidence_types(self) -> List[EvidenceType]:
        return [EvidenceType.CALIBRATION]

    def get_model_identity(self) -> str:
        return "trutina.brier.v1"

    def produce_evidence(
        self,
        request_id: str,
        claim: str,
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None
    ) -> EvidenceEnvelope:
        """Produce calibration evidence using Brier scoring."""
        forecasts = context.get("forecasts", [])
        outcomes = context.get("outcomes", [])
        
        # Generate synthetic data if not provided
        if not forecasts or not outcomes:
            forecasts, outcomes = self._generate_synthetic_data()
        
        # Compute Brier series
        outcome_values = [o["outcome_value"] for o in outcomes]
        brier_result = compute_brier_series(forecasts, outcome_values)
        brier_score = brier_result.get("series_brier", 0.25)
        
        # Compute reliability (simplified ECE)
        outcome_values = [o["outcome_value"] for o in outcomes]
        reliability = self._compute_reliability(forecasts, outcomes)
        resolution = self._compute_resolution(forecasts, outcomes)
        uncertainty = self._compute_uncertainty(outcomes)
        
        # Confidence is inverse of Brier score
        confidence = max(0.0, min(1.0, 1.0 - brier_score))
        
        envelope = EvidenceEnvelope(
            engine="trutina",
            engine_version="trutina.brier.v1",
            model_identity="trutina.brier.v1",
            request_id=request_id,
            claim=claim,
            candidate_outputs=[
                CandidateOutput(
                    answer="Well calibrated" if brier_score < 0.25 else "Needs recalibration",
                    confidence=confidence,
                    reasoning_trace=f"Brier: {brier_score:.3f}, Reliability: {reliability:.3f}, Resolution: {resolution:.3f}",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.CALIBRATION,
            reasoning_steps=[],
            relations=[],
            confidence=confidence,
            uncertainty=brier_score,
            decision_margin=0.0,
            entropy=uncertainty,
            provenance={
                "source": "trutina.brier.v1",
                "method": "brier_calibration",
                "brier_score": round(brier_score, 6),
                "reliability": round(reliability, 6),
                "resolution": round(resolution, 6),
                "uncertainty": round(uncertainty, 6),
                "calibration_method": "PLATT",
                "regimes_tested": ["stable"],
                "authority": "advisory",
                "semantic_truth": False,
                "influence_policy": "NONE",
                "valid_for_forecast": False,
                "lane": "shadow",
            }
        )
        return envelope

    def _generate_synthetic_data(self) -> tuple:
        """Generate synthetic forecasts and outcomes for testing."""
        random.seed(42)
        forecasts = []
        outcomes = []
        
        for i in range(100):
            # Generate realistic probabilities
            prob = random.uniform(0.1, 0.9)
            forecasts.append({
                "forecast_id": f"f{i}",
                "probability": prob,
                "signal_key": f"signal_{i % 10}",
                "mapping_version": "v1"
            })
            # Outcome based on probability with some noise
            outcome = 1 if random.random() < prob else 0
            outcomes.append({
                "forecast_id": f"f{i}",
                "outcome_value": outcome,
                "settlement_id": f"s{i}"
            })
        
        return forecasts, outcomes

    def _compute_reliability(self, forecasts: List[Dict], outcomes: List[Dict]) -> float:
        """Compute Expected Calibration Error (ECE) as reliability metric."""
        if not forecasts or not outcomes:
            return 0.0
        
        # Bin predictions
        bins = 10
        bin_counts = [0] * bins
        bin_conf = [0.0] * bins
        bin_acc = [0.0] * bins
        
        outcome_map = {o["forecast_id"]: o["outcome_value"] for o in outcomes}
        
        for fc in forecasts:
            fid = fc["forecast_id"]
            if fid not in outcome_map:
                continue
            prob = fc["probability"]
            outcome = outcome_map[fid]
            bin_idx = min(int(prob * 10), 9)
            bin_counts[bin_idx] += 1
            bin_conf[bin_idx] += prob
            bin_acc[bin_idx] += outcome
        
        ece = 0.0
        total = sum(bin_counts)
        if total == 0:
            return 0.0
        
        for i in range(bins):
            if bin_counts[i] > 0:
                avg_conf = bin_conf[i] / bin_counts[i]
                avg_acc = bin_acc[i] / bin_counts[i]
                ece += (bin_counts[i] / total) * abs(avg_conf - avg_acc)
        
        return round(ece, 6)

    def _compute_resolution(self, forecasts: List[Dict], outcomes: List[Dict]) -> float:
        """Compute resolution component of Brier decomposition."""
        if not forecasts or not outcomes:
            return 0.0
        
        outcome_map = {o["forecast_id"]: o["outcome_value"] for o in outcomes}
        
        bins = 10
        bin_counts = [0] * bins
        bin_acc = [0.0] * bins
        
        for fc in forecasts:
            fid = fc["forecast_id"]
            if fid not in outcome_map:
                continue
            prob = fc["probability"]
            outcome = outcome_map[fid]
            bin_idx = min(int(prob * 10), 9)
            bin_counts[bin_idx] += 1
            bin_acc[bin_idx] += outcome
        
        overall_rate = sum(outcome_map.values()) / len(outcome_map) if outcome_map else 0.5
        resolution = 0.0
        total = sum(bin_counts)
        
        for i in range(bins):
            if bin_counts[i] > 0:
                bin_rate = bin_acc[i] / bin_counts[i]
                resolution += (bin_counts[i] / total) * ((bin_rate - overall_rate) ** 2)
        
        return round(resolution, 6)

    def _compute_uncertainty(self, outcomes: List[Dict]) -> float:
        """Compute uncertainty (outcome entropy)."""
        if not outcomes:
            return 0.0
        
        n = len(outcomes)
        pos = sum(o["outcome_value"] for o in outcomes)
        if n == 0:
            return 0.0
        rate = pos / n
        if rate == 0 or rate == 1:
            return 0.0
        return round(-rate * math.log2(rate) - (1 - rate) * math.log2(1 - rate), 6)


if __name__ == "__main__":
    provider = TrutinaEvidenceProvider()
    print(f"Engine: {provider.engine_name}")
    print(f"Version: {provider.engine_version}")
    print(f"Types: {[t.value for t in provider.supported_evidence_types]}")
    
    envelope = provider.produce_evidence(
        request_id="test-001",
        claim="Test calibration",
        context={}
    )
    print(f"Evidence type: {envelope.evidence_type}")
    print(f"Confidence: {envelope.confidence:.3f}")
    print(f"Provenance keys: {list(envelope.provenance.keys())}")