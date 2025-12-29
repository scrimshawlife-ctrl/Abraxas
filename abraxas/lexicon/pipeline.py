"""
DCE ↔ SCO/STI/RDV Integration Pipeline

Connects Domain Compression Engines with existing linguistic pipeline:
- DCE provides domain-specific token weights and lifecycle states
- SCO uses DCE to detect symbolic compression events
- STI leverages DCE for transparency calculations
- RDV consumes DCE signals for affect direction

Flow: Tokens → DCE Compression → STI/RDV → SCO → Events
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from abraxas.core.provenance import Provenance
from abraxas.lexicon.dce import (
    DCECompressionResult,
    DomainCompressionEngine,
    LifecycleState,
)
from abraxas.lexicon.operators import DomainOperatorRegistry, DomainSignal


@dataclass(frozen=True)
class DCEPipelineInput:
    """Input to DCE-enhanced linguistic pipeline."""

    domain: str
    tokens: List[str]
    subdomain: Optional[str] = None
    version: Optional[str] = None
    run_id: str = ""
    git_sha: Optional[str] = None


@dataclass(frozen=True)
class DCEPipelineOutput:
    """Output from DCE-enhanced linguistic pipeline."""

    domain: str
    version: str
    compression_result: DCECompressionResult
    domain_signals: Tuple[DomainSignal, ...]
    transparency_score: Optional[float] = None  # STI if calculated
    affect_direction: Optional[str] = None  # RDV if calculated
    provenance: Provenance = None  # type: ignore


class DCELinguisticPipeline:
    """
    Integrated DCE → STI/RDV → SCO pipeline.

    Orchestrates:
    1. DCE compression (with lifecycle weighting)
    2. Domain signal extraction
    3. (Optional) STI calculation using DCE weights
    4. (Optional) RDV calculation using domain signals
    5. SCO event detection (future)
    """

    def __init__(
        self,
        dce: DomainCompressionEngine,
        operator_registry: Optional[DomainOperatorRegistry] = None,
    ) -> None:
        self._dce = dce
        self._operators = operator_registry or DomainOperatorRegistry()

    def process(
        self,
        pipeline_input: DCEPipelineInput,
        *,
        calculate_transparency: bool = False,
        calculate_affect: bool = False,
    ) -> DCEPipelineOutput:
        """
        Process tokens through DCE-enhanced pipeline.

        Args:
            pipeline_input: Input tokens and domain
            calculate_transparency: Whether to calculate STI
            calculate_affect: Whether to calculate RDV

        Returns:
            DCEPipelineOutput with compression, signals, and optional STI/RDV
        """
        # 1. DCE Compression
        compression_result = self._dce.compress(
            domain=pipeline_input.domain,
            tokens=pipeline_input.tokens,
            version=pipeline_input.version,
            run_id=pipeline_input.run_id or "PIPELINE",
            git_sha=pipeline_input.git_sha,
        )

        # 2. Extract domain signals
        domain_signals = self._operators.extract_domain_signals(
            pipeline_input.domain, compression_result
        )

        # 3. (Optional) Calculate transparency using DCE weights
        transparency_score = None
        if calculate_transparency:
            transparency_score = self._calculate_transparency(compression_result)

        # 4. (Optional) Calculate affect direction using domain signals
        affect_direction = None
        if calculate_affect:
            affect_direction = self._calculate_affect(domain_signals)

        return DCEPipelineOutput(
            domain=compression_result.domain,
            version=compression_result.version,
            compression_result=compression_result,
            domain_signals=tuple(domain_signals),
            transparency_score=transparency_score,
            affect_direction=affect_direction,
            provenance=compression_result.provenance,
        )

    def _calculate_transparency(self, result: DCECompressionResult) -> float:
        """
        Calculate Symbolic Transparency Index using DCE weights.

        Leverages lifecycle states:
        - FRONT/SATURATED tokens contribute more to transparency
        - PROTO/DORMANT tokens contribute less
        """
        if not result.matched:
            return 0.0

        # Weight by lifecycle state
        weighted_sum = 0.0
        total_weight = 0.0

        for token in result.matched:
            lifecycle = result.lifecycle_info.get(token, "proto")
            weight = result.weights_out.get(token, 0.0)

            # Lifecycle transparency multipliers
            multiplier = {
                "proto": 0.5,
                "front": 1.0,
                "saturated": 0.9,
                "dormant": 0.3,
                "archived": 0.1,
            }.get(lifecycle, 0.5)

            weighted_sum += weight * multiplier
            total_weight += multiplier

        if total_weight == 0:
            return 0.0

        # Normalize to [0, 1]
        return min(1.0, weighted_sum / total_weight)

    def _calculate_affect(self, signals: List[DomainSignal]) -> str:
        """
        Calculate Replacement Direction Vector using domain signals.

        Aggregates signals to determine affective direction:
        - Positive signals (bullish, engagement) → "positive"
        - Negative signals (bearish, conspiracy) → "negative"
        - Mixed or neutral → "neutral"
        """
        if not signals:
            return "neutral"

        # Categorize signals
        positive_markers = {
            "sentiment_bullish",
            "high_engagement",
            "viral_acceleration",
        }
        negative_markers = {
            "sentiment_bearish",
            "narrative_conspiracy",
            "epistemic_contestation",
            "rhetoric_populist",
        }

        positive_strength = sum(
            s.strength for s in signals if s.signal_type in positive_markers
        )
        negative_strength = sum(
            s.strength for s in signals if s.signal_type in negative_markers
        )

        # Determine direction
        if abs(positive_strength - negative_strength) < 0.2:
            return "neutral"
        elif positive_strength > negative_strength:
            return "positive"
        else:
            return "negative"


@dataclass(frozen=True)
class DCEFeedbackLoop:
    """
    Feedback loop: SCO events → DCE evolution.

    When SCO detects compression events, feed back to DCE to:
    - Add new tokens (lifecycle: PROTO)
    - Promote tokens (PROTO → FRONT)
    - Adjust weights based on observed compression
    """

    domain: str
    observed_compressions: List[str]  # Tokens that showed compression
    lifecycle_transitions: Dict[str, LifecycleState]  # Token → new state
    weight_adjustments: Dict[str, float]  # Token → new weight
    reason: str


class DCEFeedbackProcessor:
    """Processes SCO feedback into DCE evolution events."""

    def __init__(self, dce: DomainCompressionEngine) -> None:
        self._dce = dce

    def process_feedback(
        self,
        feedback: DCEFeedbackLoop,
        current_version: str,
        next_version: str,
        run_id: str,
    ) -> None:
        """
        Process feedback loop to evolve DCE pack.

        Creates new DCE version incorporating observed compression events.
        """
        from abraxas.lexicon.dce import DCEEntry, EvolutionReason

        # Build changes dict
        changes: Dict[str, DCEEntry] = {}

        # Add/update observed compressions
        for token in feedback.observed_compressions:
            lifecycle = feedback.lifecycle_transitions.get(token, LifecycleState.PROTO)
            weight = feedback.weight_adjustments.get(token, 0.5)

            changes[token] = DCEEntry(
                token=token,
                weight=weight,
                lifecycle_state=lifecycle,
                domain=feedback.domain,
                subdomain=None,
                meta={"origin": "sco_feedback", "reason": feedback.reason},
            )

        # Evolve lexicon
        reason = EvolutionReason.COMPRESSION_OBSERVED
        self._dce.evolve(
            domain=feedback.domain,
            from_version=current_version,
            to_version=next_version,
            changes=changes,
            removals=[],
            reason=reason,
            run_id=run_id,
        )


# Integration helpers

def create_integrated_pipeline(
    dce: DomainCompressionEngine,
) -> DCELinguisticPipeline:
    """
    Create fully integrated DCE → STI/RDV → SCO pipeline.

    Returns:
        Configured DCELinguisticPipeline ready for use
    """
    operator_registry = DomainOperatorRegistry()
    return DCELinguisticPipeline(dce=dce, operator_registry=operator_registry)


def process_tokens_with_dce(
    dce: DomainCompressionEngine,
    domain: str,
    tokens: List[str],
    run_id: str,
    *,
    with_transparency: bool = True,
    with_affect: bool = True,
) -> DCEPipelineOutput:
    """
    Convenience function: process tokens through integrated pipeline.

    Args:
        dce: Domain Compression Engine instance
        domain: Domain to compress against
        tokens: Input tokens
        run_id: Run identifier for provenance
        with_transparency: Calculate STI
        with_affect: Calculate RDV

    Returns:
        Complete pipeline output with compression, signals, STI, RDV
    """
    pipeline = create_integrated_pipeline(dce)
    pipeline_input = DCEPipelineInput(
        domain=domain,
        tokens=tokens,
        run_id=run_id,
    )

    return pipeline.process(
        pipeline_input,
        calculate_transparency=with_transparency,
        calculate_affect=with_affect,
    )
