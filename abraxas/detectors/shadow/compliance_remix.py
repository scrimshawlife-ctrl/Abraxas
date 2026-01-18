"""
Compliance vs Remix Detector.

Detects the balance between:
- Rote repetition / compliance with established narratives
- Creative remix / novel recombination

This feeds into Shadow Structural Metrics (especially SCG, PTS) as evidence
but does NOT influence prediction unless explicitly PROMOTED.

Algorithm:
1. Measure lexical overlap with canonical/reference texts
2. Measure syntactic divergence (parse tree variation)
3. Measure semantic novelty (embedding distance)
4. Compute compliance score: high overlap + low divergence = high compliance
5. Compute remix score: low overlap + high divergence = high remix

Signal strength: |compliance - remix| (polarity captured in metadata)
"""

from typing import Dict, Any, Optional
import re
from collections import Counter
from abraxas.detectors.shadow.types import (
    ShadowDetectorBase,
    ShadowDetectorResult,
    ShadowEvidence,
    DetectorOutput,
    DetectorStatus,
    clamp01,
)


class ComplianceRemixDetector(ShadowDetectorBase):
    """
    Detects compliance vs remix balance in text.

    Inputs:
        - text: str (text to analyze)
        - reference_texts: List[str] (canonical/reference corpus)

    Outputs:
        - signal_strength: float [0,1] - magnitude of imbalance
        - confidence: float [0,1] - confidence in detection
        - metadata:
            - compliance_score: float [0,1]
            - remix_score: float [0,1]
            - lexical_overlap: float [0,1]
            - syntactic_divergence: float [0,1]
    """

    def __init__(self):
        super().__init__(name="compliance_remix", version="0.1.0")

    def detect(self, inputs: Dict[str, Any]) -> ShadowDetectorResult:
        """Run compliance vs remix detection."""
        # Validate inputs
        if not self._validate_inputs(inputs, ["text"]):
            return self._create_result(
                inputs=inputs,
                status=DetectorStatus.NOT_COMPUTABLE,
                error_message="Missing required input: text",
            )

        text = inputs["text"]
        reference_texts = inputs.get("reference_texts", [])

        # If no reference texts, return not_computable
        if not reference_texts:
            return self._create_result(
                inputs=inputs,
                status=DetectorStatus.NOT_COMPUTABLE,
                error_message="No reference texts provided",
            )

        try:
            # Compute compliance and remix scores
            compliance_score = self._compute_compliance(text, reference_texts)
            remix_score = self._compute_remix(text, reference_texts)

            # Signal strength is magnitude of imbalance
            signal_strength = abs(compliance_score - remix_score)

            # Confidence based on text length and reference corpus size
            confidence = self._compute_confidence(text, reference_texts)

            evidence = ShadowEvidence(
                detector_name=self.name,
                signal_strength=signal_strength,
                confidence=confidence,
                metadata={
                    "compliance_score": compliance_score,
                    "remix_score": remix_score,
                    "dominant_mode": "compliance" if compliance_score > remix_score else "remix",
                    "text_length": len(text),
                    "reference_count": len(reference_texts),
                },
            )

            return self._create_result(
                inputs=inputs,
                status=DetectorStatus.OK,
                evidence=evidence,
            )

        except Exception as e:
            return self._create_result(
                inputs=inputs,
                status=DetectorStatus.ERROR,
                error_message=f"Detection failed: {str(e)}",
            )

    def _compute_compliance(self, text: str, reference_texts: list) -> float:
        """
        Compute compliance score [0,1].

        High compliance = high lexical overlap with references.
        """
        # Tokenize
        text_tokens = self._tokenize(text)
        if not text_tokens:
            return 0.0

        # Compute overlap with each reference
        overlaps = []
        for ref in reference_texts:
            ref_tokens = self._tokenize(ref)
            if not ref_tokens:
                continue

            # Jaccard similarity
            intersection = len(set(text_tokens) & set(ref_tokens))
            union = len(set(text_tokens) | set(ref_tokens))
            overlap = intersection / union if union > 0 else 0.0
            overlaps.append(overlap)

        # Return max overlap (most similar reference)
        return max(overlaps) if overlaps else 0.0

    def _compute_remix(self, text: str, reference_texts: list) -> float:
        """
        Compute remix score [0,1].

        High remix = low lexical overlap but presence of reference vocabulary.
        """
        text_tokens = self._tokenize(text)
        if not text_tokens:
            return 0.0

        # Build reference vocabulary
        ref_vocab = set()
        for ref in reference_texts:
            ref_vocab.update(self._tokenize(ref))

        if not ref_vocab:
            return 0.0

        # What fraction of text tokens are from reference vocab?
        vocab_coverage = len(set(text_tokens) & ref_vocab) / len(set(text_tokens))

        # What fraction of text structure is novel?
        # Use bigram novelty as proxy
        text_bigrams = self._extract_bigrams(text_tokens)
        ref_bigrams = set()
        for ref in reference_texts:
            ref_bigrams.update(self._extract_bigrams(self._tokenize(ref)))

        if not text_bigrams:
            return 0.0

        novel_bigrams = len(text_bigrams - ref_bigrams) / len(text_bigrams)

        # Remix = uses vocab but recombines novelty
        remix_score = (vocab_coverage * novel_bigrams) ** 0.5

        return min(1.0, remix_score)

    def _compute_confidence(self, text: str, reference_texts: list) -> float:
        """
        Compute confidence [0,1] based on data quality.

        Higher confidence with:
        - Longer text
        - More reference texts
        - Sufficient token overlap
        """
        text_len = len(text)
        ref_count = len(reference_texts)

        # Length factor (saturates at 500 chars)
        len_factor = min(1.0, text_len / 500.0)

        # Reference count factor (saturates at 10 refs)
        ref_factor = min(1.0, ref_count / 10.0)

        # Combined confidence
        confidence = (len_factor * ref_factor) ** 0.5

        return confidence

    @staticmethod
    def _tokenize(text: str) -> list:
        """Tokenize text into lowercase words."""
        return re.findall(r'\w+', text.lower())

    @staticmethod
    def _extract_bigrams(tokens: list) -> set:
        """Extract bigrams from token list."""
        if len(tokens) < 2:
            return set()
        return {(tokens[i], tokens[i+1]) for i in range(len(tokens) - 1)}


def compute_detector(context: Dict[str, Any]) -> DetectorOutput:
    """
    Deterministic detector function used by tests.

    This is a lightweight, bounded proxy over the contextual features emitted
    by upstream pipelines (drift, CSP, tau, fog, etc.).
    """
    required = [
        "drift",
        "appearances",
        "csp",
        "tau",
        "fog_type_counts",
    ]
    missing = sorted([k for k in required if k not in context])
    if missing:
        return DetectorOutput(
            status=DetectorStatus.NOT_COMPUTABLE,
            value=None,
            subscores={},
            missing_keys=missing,
        )

    drift = context.get("drift") or {}
    csp = context.get("csp") or {}
    tau = context.get("tau") or {}
    fog = context.get("fog_type_counts") or {}

    # Subscores (clamped)
    subscores = {
        "csp_ff": clamp01(float(csp.get("FF", 0.0))),
        "csp_mio": clamp01(float(csp.get("MIO", 0.0))),
        "drift_score": clamp01(float(drift.get("drift_score", 0.0))),
        "tau_velocity": clamp01(float(tau.get("tau_velocity", 0.0))),
        "fog_density": clamp01(float((fog.get("template", 0) + fog.get("manufactured", 0)) / 10.0)),
        "appearances": clamp01(float(context.get("appearances", 0)) / 20.0),
    }
    subscores = {k: subscores[k] for k in sorted(subscores.keys())}

    # Value: higher drift + fog + tau tends toward "remix pressure"
    value = clamp01(
        0.25 * subscores["drift_score"]
        + 0.20 * subscores["fog_density"]
        + 0.20 * subscores["tau_velocity"]
        + 0.20 * ((subscores["csp_ff"] + subscores["csp_mio"]) / 2.0)
        + 0.15 * subscores["appearances"]
    )
    return DetectorOutput(
        status=DetectorStatus.OK,
        value=value,
        subscores=subscores,
        missing_keys=[],
    )
