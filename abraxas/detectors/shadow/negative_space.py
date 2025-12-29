"""Negative Space / Silence Detector

Detects topic dropout, visibility asymmetry, and abnormal silences.

Uses real envelope fields:
- symbol_pool (events with narrative_id, topic, theme)
- history (previous symbol pools for baseline comparison)
- source distribution (from FVC)
- timestamps for mention gap calculation

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


def extract_inputs(
    context: dict[str, Any], history: Optional[list[dict[str, Any]]] = None
) -> dict[str, Any]:
    """Extract inputs from context and history.

    Args:
        context: Current envelope context
        history: Previous envelopes for baseline comparison

    Returns:
        Extracted inputs dict
    """
    inputs: dict[str, Any] = {}

    # Current narratives/topics from symbol pool
    symbol_pool = context.get("symbol_pool", [])
    current_narratives = set()
    current_sources = set()

    for event in symbol_pool:
        # Extract narrative/topic ID
        narrative = event.get("narrative_id") or event.get("topic") or event.get("theme")
        if narrative:
            current_narratives.add(str(narrative))

        # Extract source for visibility asymmetry
        source = event.get("source") or event.get("domain")
        if source:
            if isinstance(source, dict):
                source_id = source.get("domain") or source.get("url") or str(source)
                current_sources.add(str(source_id))
            else:
                current_sources.add(str(source))

    inputs["current_narratives"] = sorted(current_narratives)
    inputs["current_sources"] = sorted(current_sources)
    inputs["current_count"] = len(current_narratives)

    # Baseline narratives from history
    if history:
        baseline_narratives = set()
        historical_sources = set()

        for hist_context in history:
            hist_pool = hist_context.get("symbol_pool", [])
            for event in hist_pool:
                narrative = event.get("narrative_id") or event.get("topic") or event.get("theme")
                if narrative:
                    baseline_narratives.add(str(narrative))

                source = event.get("source") or event.get("domain")
                if source:
                    if isinstance(source, dict):
                        source_id = source.get("domain") or source.get("url") or str(source)
                        historical_sources.add(str(source_id))
                    else:
                        historical_sources.add(str(source))

        inputs["baseline_narratives"] = sorted(baseline_narratives)
        inputs["baseline_sources"] = sorted(historical_sources)
        inputs["baseline_count"] = len(baseline_narratives)
        inputs["history_length"] = len(history)
    else:
        inputs["baseline_narratives"] = []
        inputs["baseline_sources"] = []
        inputs["baseline_count"] = 0
        inputs["history_length"] = 0

    # Source distribution (from FVC if available)
    source_dist = context.get("source_distribution", {})
    if isinstance(source_dist, dict):
        inputs["source_distribution"] = dict(source_dist)
    else:
        inputs["source_distribution"] = {}

    # Timestamps for mention gap calculation
    current_timestamp = context.get("timestamp") or context.get("observed_at_utc")
    inputs["current_timestamp"] = str(current_timestamp) if current_timestamp else ""

    return inputs


def get_default_config() -> dict[str, Any]:
    """Get default configuration for detector.

    Returns:
        Config dict with thresholds
    """
    return {
        "topic_dropout_weight": 0.50,
        "visibility_asymmetry_weight": 0.30,
        "mention_gap_weight": 0.20,
        # Thresholds
        "min_baseline_strength": 0.1,  # Minimum baseline presence to count as dropout
        "min_history_length": 3,  # Minimum history entries for reliable baseline
        "asymmetry_threshold": 0.3,  # Min asymmetry to flag
        "expected_halflife_hours": 48.0,  # Expected mention halflife (2 days)
    }


def compute(
    inputs: dict[str, Any], config: dict[str, Any]
) -> tuple[float, dict[str, Any]]:
    """Compute Negative Space / Silence detection.

    Args:
        inputs: Extracted inputs from envelope and history
        config: Configuration dict

    Returns:
        Tuple of (overall_value [0,1], metadata dict)

    Higher values indicate more significant silences/dropouts.
    """
    # Extract config
    dropout_weight = float(config.get("topic_dropout_weight", 0.50))
    asymmetry_weight = float(config.get("visibility_asymmetry_weight", 0.30))
    gap_weight = float(config.get("mention_gap_weight", 0.20))

    min_baseline_strength = float(config.get("min_baseline_strength", 0.1))
    min_history_length = int(config.get("min_history_length", 3))
    asymmetry_threshold = float(config.get("asymmetry_threshold", 0.3))

    # Extract inputs
    current_narratives = set(inputs.get("current_narratives", []))
    baseline_narratives = set(inputs.get("baseline_narratives", []))
    current_sources = set(inputs.get("current_sources", []))
    baseline_sources = set(inputs.get("baseline_sources", []))
    history_length = int(inputs.get("history_length", 0))
    current_count = int(inputs.get("current_count", 0))
    baseline_count = int(inputs.get("baseline_count", 0))

    # Initialize subscores
    topic_dropout_score = 0.0
    visibility_asymmetry_score = 0.0
    mention_gap_halflife_score = 0.0

    # --- Topic Dropout Score ---
    if baseline_count > 0 and history_length >= min_history_length:
        # Find narratives present in baseline but absent now
        dropped_narratives = baseline_narratives - current_narratives

        # Filter by minimum baseline strength
        # (all narratives in baseline are considered strong if from sufficient history)
        significant_dropouts = dropped_narratives

        # Calculate dropout rate
        dropout_rate = len(significant_dropouts) / baseline_count
        topic_dropout_score = clamp01(dropout_rate)

        # Boost if baseline was large and current is small
        if baseline_count >= 5 and current_count <= 2:
            topic_dropout_score = clamp01(topic_dropout_score + 0.3)
    else:
        # Insufficient history
        topic_dropout_score = 0.0

    # --- Visibility Asymmetry Score ---
    # Compare source coverage between baseline and current
    if len(baseline_sources) > 1 and len(current_sources) >= 1:
        # Calculate source dropout rate
        dropped_sources = baseline_sources - current_sources
        source_dropout_rate = len(dropped_sources) / len(baseline_sources)

        # Asymmetry exists if some sources drop out
        if source_dropout_rate >= asymmetry_threshold:
            visibility_asymmetry_score = clamp01(source_dropout_rate)

            # Boost if asymmetry is severe (most sources dropped)
            if source_dropout_rate >= 0.7:
                visibility_asymmetry_score = clamp01(visibility_asymmetry_score + 0.2)
    else:
        # Not enough sources to detect asymmetry
        visibility_asymmetry_score = 0.0

    # --- Mention Gap Halflife Score ---
    # If we have history, calculate time since last mention for dropped topics
    # This is a proxy: if baseline had topics and now they're gone, gap exists
    if topic_dropout_score > 0.0 and history_length >= min_history_length:
        # Normalize by history length as proxy for time
        # Longer history = longer gap (assuming history is time-ordered)
        gap_normalized = min(history_length / 10.0, 1.0)  # 10 periods = max gap
        mention_gap_halflife_score = clamp01(gap_normalized * topic_dropout_score)
    else:
        mention_gap_halflife_score = 0.0

    # --- Overall Value ---
    value = clamp01(
        dropout_weight * topic_dropout_score
        + asymmetry_weight * visibility_asymmetry_score
        + gap_weight * mention_gap_halflife_score
    )

    # Metadata
    dropped_narratives_list = sorted(baseline_narratives - current_narratives)
    dropped_sources_list = sorted(baseline_sources - current_sources)

    metadata = {
        "weights": {
            "topic_dropout": dropout_weight,
            "visibility_asymmetry": asymmetry_weight,
            "mention_gap": gap_weight,
        },
        "subscores": {
            "topic_dropout_score": topic_dropout_score,
            "visibility_asymmetry_score": visibility_asymmetry_score,
            "mention_gap_halflife_score": mention_gap_halflife_score,
        },
        "current_count": current_count,
        "baseline_count": baseline_count,
        "dropped_count": len(dropped_narratives_list),
        "dropped_narratives": dropped_narratives_list[:10],  # Limit to first 10
        "dropped_sources": dropped_sources_list,
        "history_length": history_length,
    }

    return value, metadata


def compute_detector(
    context: dict[str, Any],
    history: Optional[list[dict[str, Any]]] = None,
    config: Optional[dict[str, Any]] = None,
) -> DetectorValue:
    """Compute Negative Space / Silence detector value.

    Args:
        context: Signal envelope context
        history: History of previous envelopes (REQUIRED for meaningful detection)
        config: Optional configuration overrides

    Returns:
        DetectorValue with status, value, subscores, provenance
    """
    # Extract inputs
    inputs = extract_inputs(context, history)

    # Use provided config or defaults
    detector_config = config or get_default_config()

    # Determine which keys were used and which are missing
    required_keys = ["current_narratives", "baseline_narratives", "history_length"]
    optional_keys = [
        "current_sources",
        "baseline_sources",
        "source_distribution",
        "current_timestamp",
    ]

    used_keys = sorted([k for k in required_keys + optional_keys if k in inputs])

    # Missing keys check: history is required for meaningful detection
    min_history_length = int(detector_config.get("min_history_length", 3))
    history_length = int(inputs.get("history_length", 0))

    missing_keys = []
    if history_length < min_history_length:
        missing_keys.append("sufficient_history")

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
            "topic_dropout_score": clamp01(metadata["subscores"]["topic_dropout_score"]),
            "visibility_asymmetry_score": clamp01(
                metadata["subscores"]["visibility_asymmetry_score"]
            ),
            "mention_gap_halflife_score": clamp01(
                metadata["subscores"]["mention_gap_halflife_score"]
            ),
        }
        evidence = metadata if metadata else None

    # Create provenance
    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    provenance = DetectorProvenance(
        detector_id=DetectorId.NEGATIVE_SPACE.value,
        used_keys=used_keys,
        missing_keys=sorted(missing_keys),
        history_len=history_length,
        envelope_version=context.get("version"),
        inputs_hash=hash_canonical_json(inputs),
        config_hash=hash_canonical_json(detector_config),
        computed_at_utc=now_utc,
        seed_compliant=True,
        no_influence_guarantee=True,
    )

    return DetectorValue(
        id=DetectorId.NEGATIVE_SPACE,
        status=status,
        value=value,
        subscores=subscores,
        missing_keys=sorted(missing_keys),
        evidence=evidence,
        provenance=provenance,
        bounds=(0.0, 1.0),
    )
