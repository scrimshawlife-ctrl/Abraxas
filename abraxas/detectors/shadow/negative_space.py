"""
Negative Space / Silence Detector.

Detects what is NOT being said:
- Topic dropout (expected topics missing from discourse)
- Visibility asymmetry (some topics amplified, others suppressed)
- Conspicuous absence (topics that should be present but aren't)

This feeds into Shadow Structural Metrics (especially NOR, FVC) as evidence
but does NOT influence prediction unless explicitly PROMOTED.

Algorithm:
1. Require a baseline/reference corpus defining expected topics
2. Extract topic distribution from reference
3. Extract topic distribution from observed text
4. Compute divergence (KL divergence, Jensen-Shannon distance)
5. Identify dropped topics (high in reference, low/absent in observed)
6. Signal strength = magnitude of divergence
"""

from typing import Dict, Any, List, Set
import re
import math
from collections import Counter
from abraxas.detectors.shadow.types import (
    ShadowDetectorBase,
    ShadowDetectorResult,
    ShadowEvidence,
    DetectorOutput,
    DetectorStatus,
    clamp01,
)


class NegativeSpaceDetector(ShadowDetectorBase):
    """
    Detects negative space / topic dropout.

    Inputs:
        - text: str (observed text)
        - baseline_texts: List[str] (reference corpus defining expected topics)
        - topic_keywords: Dict[str, List[str]] (optional: explicit topic->keywords mapping)

    Outputs:
        - signal_strength: float [0,1] - magnitude of topic divergence
        - confidence: float [0,1] - confidence in detection
        - metadata:
            - dropped_topics: List[str] (topics present in baseline but absent in text)
            - amplified_topics: List[str] (topics over-represented vs baseline)
            - divergence_score: float (KL-like divergence measure)
    """

    def __init__(self):
        super().__init__(name="negative_space", version="0.1.0")

    def detect(self, inputs: Dict[str, Any]) -> ShadowDetectorResult:
        """Run negative space detection."""
        # Validate inputs
        if not self._validate_inputs(inputs, ["text"]):
            return self._create_result(
                inputs=inputs,
                status="not_computable",
                error_message="Missing required input: text",
            )

        text = inputs["text"]
        baseline_texts = inputs.get("baseline_texts", [])
        topic_keywords = inputs.get("topic_keywords", None)

        if not baseline_texts:
            return self._create_result(
                inputs=inputs,
                status="not_computable",
                error_message="No baseline texts provided",
            )

        try:
            # Extract topic distributions
            if topic_keywords:
                # Use explicit topic keywords
                baseline_dist = self._topic_distribution_explicit(baseline_texts, topic_keywords)
                observed_dist = self._topic_distribution_explicit([text], topic_keywords)
            else:
                # Use lexical frequency as proxy
                baseline_dist = self._topic_distribution_lexical(baseline_texts)
                observed_dist = self._topic_distribution_lexical([text])

            # Compute divergence
            divergence = self._jensen_shannon_divergence(baseline_dist, observed_dist)

            # Identify dropped and amplified topics
            dropped_topics = self._find_dropped_topics(baseline_dist, observed_dist, threshold=0.5)
            amplified_topics = self._find_amplified_topics(baseline_dist, observed_dist, threshold=2.0)

            # Signal strength = divergence (already in [0,1])
            signal_strength = divergence

            # Confidence based on data quality
            confidence = self._compute_confidence(text, baseline_texts)

            evidence = ShadowEvidence(
                detector_name=self.name,
                signal_strength=signal_strength,
                confidence=confidence,
                metadata={
                    "dropped_topics": dropped_topics[:5],  # Top 5
                    "amplified_topics": amplified_topics[:5],  # Top 5
                    "divergence_score": divergence,
                    "baseline_count": len(baseline_texts),
                },
            )

            return self._create_result(
                inputs=inputs,
                status="computed",
                evidence=evidence,
            )

        except Exception as e:
            return self._create_result(
                inputs=inputs,
                status="error",
                error_message=f"Detection failed: {str(e)}",
            )

    def _topic_distribution_explicit(
        self, texts: List[str], topic_keywords: Dict[str, List[str]]
    ) -> Dict[str, float]:
        """
        Compute topic distribution using explicit keyword mapping.

        Returns:
            {topic: probability}
        """
        topic_counts = Counter()
        total_matches = 0

        for text in texts:
            text_lower = text.lower()
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                    topic_counts[topic] += matches
                    total_matches += matches

        # Normalize to probabilities
        if total_matches == 0:
            return {topic: 1.0 / len(topic_keywords) for topic in topic_keywords}

        return {topic: count / total_matches for topic, count in topic_counts.items()}

    def _topic_distribution_lexical(self, texts: List[str]) -> Dict[str, float]:
        """
        Compute topic distribution using top-N lexical items as proxy.

        Returns:
            {word: probability}
        """
        word_counts = Counter()

        for text in texts:
            words = re.findall(r'\b\w+\b', text.lower())
            # Filter out stopwords (simple list)
            stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"}
            words = [w for w in words if w not in stopwords and len(w) > 3]
            word_counts.update(words)

        # Take top 50 words as "topics"
        total = sum(word_counts.values())
        if total == 0:
            return {}

        top_words = word_counts.most_common(50)
        return {word: count / total for word, count in top_words}

    def _jensen_shannon_divergence(
        self, dist1: Dict[str, float], dist2: Dict[str, float]
    ) -> float:
        """
        Compute Jensen-Shannon divergence between two distributions.

        JSD is symmetric and bounded [0,1].
        """
        # Get all topics
        all_topics = set(dist1.keys()) | set(dist2.keys())

        if not all_topics:
            return 0.0

        # Build probability vectors (with smoothing)
        epsilon = 1e-10
        p = [dist1.get(t, 0.0) + epsilon for t in all_topics]
        q = [dist2.get(t, 0.0) + epsilon for t in all_topics]

        # Normalize
        p_sum = sum(p)
        q_sum = sum(q)
        p = [x / p_sum for x in p]
        q = [x / q_sum for x in q]

        # Compute M = (P + Q) / 2
        m = [(p[i] + q[i]) / 2.0 for i in range(len(p))]

        # KL(P || M)
        kl_pm = sum(p[i] * math.log2(p[i] / m[i]) for i in range(len(p)))

        # KL(Q || M)
        kl_qm = sum(q[i] * math.log2(q[i] / m[i]) for i in range(len(q)))

        # JSD = (KL(P||M) + KL(Q||M)) / 2
        jsd = (kl_pm + kl_qm) / 2.0

        # Normalize to [0,1] (JSD is bounded by log2(2) = 1)
        return min(1.0, jsd)

    def _find_dropped_topics(
        self, baseline: Dict[str, float], observed: Dict[str, float], threshold: float = 0.5
    ) -> List[str]:
        """
        Find topics present in baseline but dropped/reduced in observed.

        Args:
            baseline: Baseline distribution
            observed: Observed distribution
            threshold: Ratio threshold (observed/baseline < threshold → dropped)

        Returns:
            List of dropped topic names
        """
        dropped = []
        for topic, baseline_prob in baseline.items():
            if baseline_prob < 0.01:  # Skip very rare topics
                continue
            observed_prob = observed.get(topic, 0.0)
            if observed_prob == 0.0 or (observed_prob / baseline_prob) < threshold:
                dropped.append(topic)

        return sorted(dropped, key=lambda t: baseline.get(t, 0.0), reverse=True)

    def _find_amplified_topics(
        self, baseline: Dict[str, float], observed: Dict[str, float], threshold: float = 2.0
    ) -> List[str]:
        """
        Find topics amplified in observed vs baseline.

        Args:
            baseline: Baseline distribution
            observed: Observed distribution
            threshold: Ratio threshold (observed/baseline > threshold → amplified)

        Returns:
            List of amplified topic names
        """
        amplified = []
        for topic, observed_prob in observed.items():
            if observed_prob < 0.01:  # Skip very rare topics
                continue
            baseline_prob = baseline.get(topic, 0.0)
            if baseline_prob > 0 and (observed_prob / baseline_prob) > threshold:
                amplified.append(topic)

        return sorted(amplified, key=lambda t: observed.get(t, 0.0), reverse=True)

    def _compute_confidence(self, text: str, baseline_texts: list) -> float:
        """
        Compute confidence [0,1] based on data quality.

        Higher confidence with:
        - Longer text
        - More baseline texts
        """
        text_len = len(text)
        baseline_count = len(baseline_texts)

        # Length factor (saturates at 500 chars)
        len_factor = min(1.0, text_len / 500.0)

        # Baseline count factor (saturates at 10 texts)
        baseline_factor = min(1.0, baseline_count / 10.0)

        # Combined confidence
        confidence = (len_factor * baseline_factor) ** 0.5

        return confidence


def compute_detector(context: Dict[str, Any], history: List[Dict[str, Any]] | None = None) -> DetectorOutput:
    """
    Deterministic negative-space proxy used by tests.

    Interprets `symbol_pool` entries as narratives with a `narrative_id` key and
    measures topic dropout relative to a historical baseline.
    """
    if history is None:
        history = []

    if "symbol_pool" not in context:
        return DetectorOutput(
            status=DetectorStatus.NOT_COMPUTABLE,
            value=None,
            subscores={},
            missing_keys=["symbol_pool"],
        )

    # Baseline topics from history
    baseline_topics: Set[str] = set()
    for h in history:
        pool = h.get("symbol_pool") if isinstance(h, dict) else None
        if not isinstance(pool, list):
            continue
        for item in pool:
            if isinstance(item, dict) and str(item.get("narrative_id", "")).strip():
                baseline_topics.add(str(item["narrative_id"]))

    if not baseline_topics:
        return DetectorOutput(
            status=DetectorStatus.NOT_COMPUTABLE,
            value=None,
            subscores={},
            missing_keys=["history.symbol_pool"],
        )

    current_topics: Set[str] = set()
    cur_pool = context.get("symbol_pool") or []
    if isinstance(cur_pool, list):
        for item in cur_pool:
            if isinstance(item, dict) and str(item.get("narrative_id", "")).strip():
                current_topics.add(str(item["narrative_id"]))

    overlap = len(baseline_topics & current_topics)
    dropout = 1.0 - (overlap / float(len(baseline_topics)))

    subscores = {
        "baseline_topics": clamp01(len(baseline_topics) / 100.0),
        "current_topics": clamp01(len(current_topics) / 100.0),
        "dropout_ratio": clamp01(dropout),
    }
    subscores = {k: subscores[k] for k in sorted(subscores.keys())}

    return DetectorOutput(
        status=DetectorStatus.OK,
        value=subscores["dropout_ratio"],
        subscores=subscores,
        missing_keys=[],
    )
