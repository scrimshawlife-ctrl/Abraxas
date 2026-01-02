"""
Meta-Awareness Detector.

Detects meta-level discourse about:
- Algorithmic awareness ("the algorithm promotes...")
- Manipulation awareness ("they're trying to manipulate...")
- Filter bubble awareness ("I know I'm in an echo chamber...")
- Platform mechanics ("engagement bait", "clickbait")

This feeds into Shadow Structural Metrics (especially CLIP, NOR, FVC) as evidence
but does NOT influence prediction unless explicitly PROMOTED.

Algorithm:
1. Match meta-linguistic patterns via regex/keyword lists
2. Compute density of meta-awareness markers
3. Classify meta-awareness type (algorithmic, manipulation, filter, platform)
4. Signal strength = density of meta-markers
"""

from typing import Dict, Any, List, Tuple
import re
from abraxas.detectors.shadow.types import (
    ShadowDetectorBase,
    ShadowDetectorResult,
    ShadowEvidence,
    DetectorOutput,
    DetectorStatus,
    clamp01,
)


class MetaAwarenessDetector(ShadowDetectorBase):
    """
    Detects meta-awareness discourse in text.

    Inputs:
        - text: str (text to analyze)

    Outputs:
        - signal_strength: float [0,1] - density of meta-awareness markers
        - confidence: float [0,1] - confidence in detection
        - metadata:
            - meta_type: str (dominant meta-awareness category)
            - marker_count: int (number of markers detected)
            - marker_density: float (markers per 100 words)
            - markers: List[str] (detected marker phrases)
    """

    # Meta-awareness patterns by category
    META_PATTERNS = {
        "algorithmic": [
            r"\bthe algorithm\b",
            r"\balgorithm promotes\b",
            r"\bfor the algorithm\b",
            r"\brecommendation system\b",
            r"\bfeed shows\b",
            r"\btimeline manipulation\b",
        ],
        "manipulation": [
            r"\bmanipulat(e|ion|ing)\b",
            r"\bpropaganda\b",
            r"\bpsyops\b",
            r"\bastroturf\b",
            r"\bcoordinated campaign\b",
            r"\bthey want you to\b",
        ],
        "filter_bubble": [
            r"\becho chamber\b",
            r"\bfilter bubble\b",
            r"\bconfirmation bias\b",
            r"\bpolarization\b",
            r"\bsilo\b",
        ],
        "platform": [
            r"\bengagement bait\b",
            r"\bclickbait\b",
            r"\brage bait\b",
            r"\bviral\b",
            r"\bfor engagement\b",
            r"\bboost\b",
        ],
    }

    def __init__(self):
        super().__init__(name="meta_awareness", version="0.1.0")

    def detect(self, inputs: Dict[str, Any]) -> ShadowDetectorResult:
        """Run meta-awareness detection."""
        # Validate inputs
        if not self._validate_inputs(inputs, ["text"]):
            return self._create_result(
                inputs=inputs,
                status="not_computable",
                error_message="Missing required input: text",
            )

        text = inputs["text"]

        if not text or not text.strip():
            return self._create_result(
                inputs=inputs,
                status="not_computable",
                error_message="Empty text provided",
            )

        try:
            # Detect meta-awareness markers
            markers, meta_type = self._detect_markers(text)

            # Compute density (markers per 100 words)
            word_count = len(re.findall(r'\b\w+\b', text))
            if word_count == 0:
                marker_density = 0.0
            else:
                marker_density = (len(markers) / word_count) * 100.0

            # Signal strength (saturate at 5 markers per 100 words)
            signal_strength = min(1.0, marker_density / 5.0)

            # Confidence based on text length
            confidence = self._compute_confidence(text)

            evidence = ShadowEvidence(
                detector_name=self.name,
                signal_strength=signal_strength,
                confidence=confidence,
                metadata={
                    "meta_type": meta_type,
                    "marker_count": len(markers),
                    "marker_density": marker_density,
                    "markers": markers[:10],  # Top 10 markers
                    "word_count": word_count,
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

    def _detect_markers(self, text: str) -> Tuple[List[str], str]:
        """
        Detect meta-awareness markers in text.

        Returns:
            (markers, dominant_meta_type)
        """
        text_lower = text.lower()
        markers = []
        category_counts = {cat: 0 for cat in self.META_PATTERNS}

        for category, patterns in self.META_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    markers.extend(matches)
                    category_counts[category] += len(matches)

        # Find dominant category
        if not markers:
            dominant_type = "none"
        else:
            dominant_type = max(category_counts, key=category_counts.get)

        return markers, dominant_type

    def _compute_confidence(self, text: str) -> float:
        """
        Compute confidence [0,1] based on text length.

        Higher confidence with longer text (saturates at 200 words).
        """
        word_count = len(re.findall(r'\b\w+\b', text))
        return min(1.0, word_count / 200.0)


def compute_detector(context: Dict[str, Any]) -> DetectorOutput:
    """
    Deterministic meta-awareness proxy used by tests.

    Uses keyword density in `context["text"]` plus optional manipulation-risk hints.
    """
    text = str(context.get("text", "") or "")
    if not text.strip():
        return DetectorOutput(
            status=DetectorStatus.NOT_COMPUTABLE,
            value=None,
            subscores={},
            missing_keys=["text"],
        )

    t = text.lower()
    keywords = ["algorithm", "manufactured", "psyop", "ragebait", "bot", "clickbait", "engagement"]
    counts = {k: len(re.findall(r"\b" + re.escape(k) + r"\b", t)) for k in keywords}
    word_count = max(1, len(re.findall(r"\b\w+\b", t)))
    density = sum(counts.values()) / float(word_count)  # markers per word

    dmx = context.get("dmx") or {}
    risk = float(dmx.get("overall_manipulation_risk", 0.0) or 0.0)

    subscores = {
        "keyword_density": clamp01(density * 20.0),  # saturate ~0.05 markers/word
        "dmx_risk": clamp01(risk),
        "marker_count": clamp01(sum(counts.values()) / 20.0),
    }
    subscores = {k: subscores[k] for k in sorted(subscores.keys())}

    value = clamp01(0.7 * subscores["keyword_density"] + 0.3 * subscores["dmx_risk"])
    return DetectorOutput(
        status=DetectorStatus.OK,
        value=value,
        subscores=subscores,
        missing_keys=[],
    )
