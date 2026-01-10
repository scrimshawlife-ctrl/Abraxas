from __future__ import annotations

from typing import Any, Dict

_VOWELS = set("aeiouy")


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _approx_phoneme_count(term: str) -> int:
    cleaned = "".join(ch for ch in term.lower() if ch.isalpha())
    if not cleaned:
        return 0
    count = 0
    prev_is_vowel = False
    for ch in cleaned:
        is_vowel = ch in _VOWELS
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel
    return max(1, count)


def _edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        prev = dp[0]
        dp[0] = i
        for j, cb in enumerate(b, start=1):
            cur = dp[j]
            cost = 0 if ca == cb else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = cur
    return dp[-1]


def stickiness(
    *,
    term_raw: str,
    base_term: str,
    collision_penalty: float,
) -> float:
    len_chars = len(term_raw)
    phoneme_count = _approx_phoneme_count(term_raw)
    edit_distance = _edit_distance(term_raw.lower(), base_term.lower()) if base_term else 0
    collision_penalty = _clamp(collision_penalty, 0.0, 0.4)
    score = 1.0 - (len_chars / 18.0) - (phoneme_count / 12.0) - (edit_distance * 0.15) - collision_penalty
    return _clamp(score)


def plausibility(
    *,
    base_term_exists: float,
    morphological_validity: float,
    attested_patterns_score: float,
    semantic_coherence: float,
) -> float:
    score = (
        base_term_exists * 0.35
        + _clamp(morphological_validity) * 0.25
        + _clamp(attested_patterns_score) * 0.20
        + _clamp(semantic_coherence) * 0.20
    )
    return _clamp(score)


def compression_gain(
    *,
    expanded_phrase_len: float,
    term_len: float,
    semantic_density: float,
) -> float:
    score = (expanded_phrase_len / 8.0) * _clamp(semantic_density) * (1.0 - term_len / 20.0)
    return _clamp(score)


def adoption_pressure(
    *,
    motif_overlap_count: float,
    domain_crossings: float,
    event_intensity: float,
    platform_velocity: float,
) -> float:
    score = (
        motif_overlap_count * 0.15
        + domain_crossings * 0.20
        + _clamp(event_intensity) * 0.35
        + _clamp(platform_velocity) * 0.30
    )
    return _clamp(score)


def drift_charge(*, stickiness_score: float, plausibility_score: float, compression_gain_score: float, adoption_pressure_score: float) -> float:
    score = (
        _clamp(stickiness_score) * 0.25
        + _clamp(plausibility_score) * 0.25
        + _clamp(compression_gain_score) * 0.20
        + _clamp(adoption_pressure_score) * 0.30
    )
    return _clamp(score)


def derive_signals(term_raw: str, base_term: str, *, metrics: Dict[str, Any]) -> Dict[str, float]:
    collision_penalty = float(metrics.get("collision_penalty", 0.0) or 0.0)
    base_term_exists = float(metrics.get("base_term_exists", 0.0) or 0.0)
    morphological_validity = float(metrics.get("morphological_validity", 0.0) or 0.0)
    attested_patterns_score = float(metrics.get("attested_patterns_score", 0.0) or 0.0)
    semantic_coherence = float(metrics.get("semantic_coherence", 0.0) or 0.0)
    expanded_phrase_len = float(metrics.get("expanded_phrase_len", 0.0) or 0.0)
    semantic_density = float(metrics.get("semantic_density", 0.0) or 0.0)
    motif_overlap_count = float(metrics.get("motif_overlap_count", 0.0) or 0.0)
    domain_crossings = float(metrics.get("domain_crossings", 0.0) or 0.0)
    event_intensity = float(metrics.get("event_intensity", 0.0) or 0.0)
    platform_velocity = float(metrics.get("platform_velocity", 0.0) or 0.0)

    stickiness_score = stickiness(term_raw=term_raw, base_term=base_term, collision_penalty=collision_penalty)
    plausibility_score = plausibility(
        base_term_exists=base_term_exists,
        morphological_validity=morphological_validity,
        attested_patterns_score=attested_patterns_score,
        semantic_coherence=semantic_coherence,
    )
    compression_gain_score = compression_gain(
        expanded_phrase_len=expanded_phrase_len,
        term_len=len(term_raw),
        semantic_density=semantic_density,
    )
    adoption_pressure_score = adoption_pressure(
        motif_overlap_count=motif_overlap_count,
        domain_crossings=domain_crossings,
        event_intensity=event_intensity,
        platform_velocity=platform_velocity,
    )

    return {
        "stickiness": stickiness_score,
        "plausibility": plausibility_score,
        "compression_gain": compression_gain_score,
        "adoption_pressure": adoption_pressure_score,
    }


def compute_drift_charge_from_signals(signals: Dict[str, Any]) -> float:
    return drift_charge(
        stickiness_score=float(signals.get("stickiness", 0.0) or 0.0),
        plausibility_score=float(signals.get("plausibility", 0.0) or 0.0),
        compression_gain_score=float(signals.get("compression_gain", 0.0) or 0.0),
        adoption_pressure_score=float(signals.get("adoption_pressure", 0.0) or 0.0),
    )


def priority_score(entry: Dict[str, Any]) -> float:
    signals = entry.get("signals", {})
    drift = entry.get("drift", {})
    novelty = float(signals.get("novelty", 0.0) or 0.0)
    plausibility_score = float(signals.get("plausibility", 0.0) or 0.0)
    adoption_pressure_score = float(signals.get("adoption_pressure", 0.0) or 0.0)
    stickiness_score = float(signals.get("stickiness", 0.0) or 0.0)
    drift_charge_score = float(drift.get("drift_charge", 0.0) or 0.0)

    return (
        0.30 * plausibility_score
        + 0.25 * adoption_pressure_score
        + 0.20 * stickiness_score
        + 0.15 * drift_charge_score
        + 0.10 * novelty
    )
