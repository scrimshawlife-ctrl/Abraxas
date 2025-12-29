"""Meta-Awareness Detector

Detects meta-level discourse about manipulation, algorithms, and epistemic fatigue.

Uses real envelope fields:
- dmx (manipulation risk metrics)
- rdv axes (irony, humor, nihilism)
- efte (epistemic fatigue metrics)
- narrative manipulation metrics (RRS, CIS, EIL)
- network campaign metrics (CUS)

SHADOW-ONLY: Feeds shadow metrics as evidence, never influences decisions.
"""

from __future__ import annotations

import socket
from datetime import datetime, timezone
from typing import Any, Optional

from abraxas.core.provenance import hash_canonical_json
from abraxas.detectors.shadow.types import (
    DetectorId,
    DetectorProvenance,
    DetectorStatus,
    DetectorValue,
    clamp01,
)


def extract_inputs(context: dict[str, Any]) -> dict[str, Any]:
    """Extract inputs from context envelope.

    Looks for real fields from DMX, RDV, EFTE, and integrity metrics.

    Args:
        context: Envelope context dict

    Returns:
        Extracted inputs dict
    """
    inputs: dict[str, Any] = {}

    # DMX (Disinformation Metrics) - from disinfo/metrics.py
    dmx_data = context.get("dmx", {})
    if isinstance(dmx_data, dict):
        inputs["dmx_overall"] = float(dmx_data.get("overall_manipulation_risk", 0.0))
        inputs["dmx_bucket"] = str(dmx_data.get("bucket", "UNKNOWN")).upper()

    # RDV axes (Replacement Direction Vector) - from linguistic/rdv.py
    rdv_data = context.get("rdv", {})
    if isinstance(rdv_data, dict):
        inputs["rdv_irony"] = float(rdv_data.get("irony", 0.0))
        inputs["rdv_humor"] = float(rdv_data.get("humor", 0.0))
        inputs["rdv_nihilism"] = float(rdv_data.get("nihilism", 0.0))

    # EFTE (Epistemic Fatigue) - from sod/efte.py
    efte_data = context.get("efte", {})
    if isinstance(efte_data, dict):
        inputs["fatigue_threshold"] = float(efte_data.get("threshold", 0.0))
        inputs["saturation_risk"] = str(efte_data.get("saturation_risk", "LOW")).upper()
        inputs["declining_engagement"] = bool(efte_data.get("declining_engagement", False))

    # Narrative manipulation metrics - from integrity/composites.py
    narrative_data = context.get("narrative_manipulation", {})
    if isinstance(narrative_data, dict):
        inputs["rrs"] = float(narrative_data.get("rrs", 0.0))  # Repetition/Redundancy Score
        inputs["cis"] = float(narrative_data.get("cis", 0.0))  # Coordination Indicator Score
        inputs["eil"] = float(narrative_data.get("eil", 0.0))  # Emotional Intensity Level

    # Network campaign metrics
    network_data = context.get("network_campaign", {})
    if isinstance(network_data, dict):
        inputs["cus"] = float(network_data.get("cus", 0.0))  # Coordination/Uniformity Score

    # Risk indices
    inputs["mri"] = float(context.get("MRI", 0.0))  # Manipulation Risk Index [0,100]
    inputs["iri"] = float(context.get("IRI", 0.0))  # Integrity Risk Index [0,100]

    # Text content for keyword detection (if available)
    inputs["text"] = str(context.get("text", ""))

    return inputs


def get_default_config() -> dict[str, Any]:
    """Get default configuration for detector.

    Returns:
        Config dict with weights and keyword lists
    """
    return {
        "manipulation_discourse_weight": 0.40,
        "algorithm_awareness_weight": 0.30,
        "fatigue_joke_weight": 0.20,
        "predictive_mockery_weight": 0.10,
        # Keyword lists (deterministic heuristics)
        "manipulation_keywords": [
            "manufactured",
            "psyop",
            "bot",
            "algo",
            "algorithm",
            "ragebait",
            "propaganda",
            "astroturf",
            "coordinated",
            "inauthentic",
        ],
        "algorithm_keywords": [
            "algorithm",
            "algo",
            "feed",
            "recommendation",
            "engagement",
            "metric",
            "optimize",
            "viral",
        ],
        "fatigue_keywords": [
            "again",
            "another",
            "tired",
            "exhausted",
            "enough",
            "over it",
            "done",
        ],
        "mockery_keywords": [
            "calling it",
            "predict",
            "bet",
            "watch",
            "incoming",
            "next",
        ],
    }


def _count_keywords(text: str, keywords: list[str]) -> int:
    """Count keyword occurrences in text (case-insensitive).

    Args:
        text: Text to search
        keywords: List of keywords

    Returns:
        Count of keyword matches
    """
    if not text:
        return 0

    text_lower = text.lower()
    count = 0
    for keyword in keywords:
        if keyword.lower() in text_lower:
            count += 1
    return count


def compute(
    inputs: dict[str, Any], config: dict[str, Any]
) -> tuple[float, dict[str, Any]]:
    """Compute Meta-Awareness detection.

    Args:
        inputs: Extracted inputs from envelope
        config: Configuration dict

    Returns:
        Tuple of (overall_value [0,1], metadata dict)

    Higher values indicate more meta-awareness about manipulation/algorithms.
    """
    # Extract config
    manipulation_weight = float(config.get("manipulation_discourse_weight", 0.40))
    algorithm_weight = float(config.get("algorithm_awareness_weight", 0.30))
    fatigue_weight = float(config.get("fatigue_joke_weight", 0.20))
    mockery_weight = float(config.get("predictive_mockery_weight", 0.10))

    manipulation_keywords = config.get("manipulation_keywords", [])
    algorithm_keywords = config.get("algorithm_keywords", [])
    fatigue_keywords = config.get("fatigue_keywords", [])
    mockery_keywords = config.get("mockery_keywords", [])

    # Extract inputs
    dmx_overall = float(inputs.get("dmx_overall", 0.0))
    dmx_bucket = str(inputs.get("dmx_bucket", "UNKNOWN"))
    rdv_irony = float(inputs.get("rdv_irony", 0.0))
    rdv_humor = float(inputs.get("rdv_humor", 0.0))
    rdv_nihilism = float(inputs.get("rdv_nihilism", 0.0))
    fatigue_threshold = float(inputs.get("fatigue_threshold", 0.0))
    saturation_risk = str(inputs.get("saturation_risk", "LOW"))
    rrs = float(inputs.get("rrs", 0.0))
    cis = float(inputs.get("cis", 0.0))
    text = str(inputs.get("text", ""))

    # Initialize subscores
    manipulation_discourse_score = 0.0
    algorithm_awareness_score = 0.0
    fatigue_joke_rate = 0.0
    predictive_mockery_rate = 0.0

    # --- Manipulation Discourse Score ---
    # Count manipulation keywords
    manip_keyword_count = _count_keywords(text, manipulation_keywords)
    if manip_keyword_count > 0:
        manipulation_discourse_score = clamp01(manip_keyword_count / 5.0)  # Normalize

    # High DMX + high CIS (coordination) suggests awareness of manipulation
    if dmx_overall > 0.5 and cis > 0.3:
        manipulation_discourse_score = clamp01(manipulation_discourse_score + 0.3)

    # Irony + high DMX suggests meta-commentary
    if rdv_irony > 0.2 and dmx_overall > 0.4:
        manipulation_discourse_score = clamp01(manipulation_discourse_score + 0.2)

    # --- Algorithm Awareness Score ---
    # Count algorithm keywords
    algo_keyword_count = _count_keywords(text, algorithm_keywords)
    if algo_keyword_count > 0:
        algorithm_awareness_score = clamp01(algo_keyword_count / 5.0)

    # High coordination (CIS) suggests awareness of algorithmic amplification
    if cis > 0.5:
        algorithm_awareness_score = clamp01(algorithm_awareness_score + 0.25)

    # --- Fatigue Joke Rate ---
    # Count fatigue keywords
    fatigue_keyword_count = _count_keywords(text, fatigue_keywords)

    # High fatigue threshold + high RRS (repetition) + humor/irony
    if fatigue_threshold > 0.5 and rrs > 0.4:
        fatigue_joke_rate = clamp01(fatigue_threshold)

    # Boost with keywords
    if fatigue_keyword_count > 0:
        fatigue_joke_rate = clamp01(fatigue_joke_rate + (fatigue_keyword_count / 5.0))

    # Humor + nihilism + fatigue = fatigue jokes
    if rdv_humor > 0.2 and rdv_nihilism > 0.2:
        fatigue_joke_rate = clamp01(fatigue_joke_rate + 0.2)

    # --- Predictive Mockery Rate ---
    # Count mockery/prediction keywords
    mockery_keyword_count = _count_keywords(text, mockery_keywords)
    if mockery_keyword_count > 0:
        predictive_mockery_rate = clamp01(mockery_keyword_count / 5.0)

    # High irony + pattern awareness (high RRS) suggests predictive mockery
    if rdv_irony > 0.3 and rrs > 0.5:
        predictive_mockery_rate = clamp01(predictive_mockery_rate + 0.25)

    # --- Overall Value ---
    value = clamp01(
        manipulation_weight * manipulation_discourse_score
        + algorithm_weight * algorithm_awareness_score
        + fatigue_weight * fatigue_joke_rate
        + mockery_weight * predictive_mockery_rate
    )

    # Metadata
    metadata = {
        "weights": {
            "manipulation_discourse": manipulation_weight,
            "algorithm_awareness": algorithm_weight,
            "fatigue_joke": fatigue_weight,
            "predictive_mockery": mockery_weight,
        },
        "subscores": {
            "manipulation_discourse_score": manipulation_discourse_score,
            "algorithm_awareness_score": algorithm_awareness_score,
            "fatigue_joke_rate": fatigue_joke_rate,
            "predictive_mockery_rate": predictive_mockery_rate,
        },
        "keyword_counts": {
            "manipulation": manip_keyword_count,
            "algorithm": algo_keyword_count,
            "fatigue": fatigue_keyword_count,
            "mockery": mockery_keyword_count,
        },
        "dmx_bucket": dmx_bucket,
        "saturation_risk": saturation_risk,
    }

    return value, metadata


def compute_detector(
    context: dict[str, Any],
    history: Optional[list[dict[str, Any]]] = None,
    config: Optional[dict[str, Any]] = None,
) -> DetectorValue:
    """Compute Meta-Awareness detector value.

    Args:
        context: Signal envelope context
        history: Optional history of previous envelopes (not used for this detector)
        config: Optional configuration overrides

    Returns:
        DetectorValue with status, value, subscores, provenance
    """
    # Extract inputs
    inputs = extract_inputs(context)

    # Use provided config or defaults
    detector_config = config or get_default_config()

    # Determine which keys were used and which are missing
    required_keys = ["text"]  # Text is required for keyword detection
    optional_keys = [
        "dmx_overall",
        "dmx_bucket",
        "rdv_irony",
        "rdv_humor",
        "rdv_nihilism",
        "fatigue_threshold",
        "saturation_risk",
        "rrs",
        "cis",
        "mri",
        "iri",
    ]

    used_keys = sorted([k for k in required_keys + optional_keys if k in inputs])
    missing_keys = sorted([k for k in required_keys if k not in inputs or not inputs[k]])

    # Compute status
    status = DetectorStatus.OK if not missing_keys else DetectorStatus.NOT_COMPUTABLE

    # Compute value if status is OK
    value: Optional[float] = None
    subscores: dict[str, float] = {}
    evidence: Optional[dict[str, Any]] = None

    if status == DetectorStatus.OK:
        computed_value, metadata = compute(inputs, detector_config)
        value = computed_value
        subscores = {
            "manipulation_discourse_score": clamp01(
                metadata["subscores"]["manipulation_discourse_score"]
            ),
            "algorithm_awareness_score": clamp01(
                metadata["subscores"]["algorithm_awareness_score"]
            ),
            "fatigue_joke_rate": clamp01(metadata["subscores"]["fatigue_joke_rate"]),
            "predictive_mockery_rate": clamp01(
                metadata["subscores"]["predictive_mockery_rate"]
            ),
        }
        evidence = metadata if metadata else None

    # Create provenance
    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    provenance = DetectorProvenance(
        detector_id=DetectorId.META_AWARENESS.value,
        used_keys=used_keys,
        missing_keys=missing_keys,
        history_len=len(history) if history else 0,
        envelope_version=context.get("version"),
        inputs_hash=hash_canonical_json(inputs),
        config_hash=hash_canonical_json(detector_config),
        computed_at_utc=now_utc,
        seed_compliant=True,
        no_influence_guarantee=True,
    )

    return DetectorValue(
        id=DetectorId.META_AWARENESS,
        status=status,
        value=value,
        subscores=subscores,
        missing_keys=missing_keys,
        evidence=evidence,
        provenance=provenance,
        bounds=(0.0, 1.0),
    )
